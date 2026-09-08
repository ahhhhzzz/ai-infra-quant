"""Bounded compatible transports. No discovery, redirects, retries, or model fallback."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from ai_infra_quant.application.paqs_e_models import (
    ModelCredentials,
    ModelDescriptor,
    ModelRegistry,
)
from ai_infra_quant.application.paqs_e_research import ResearchFailure
from ai_infra_quant.core.domain.common import utc_now
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AuxiliaryContextItem,
    PaqsEReasoningRequestV1,
    PromptPackage,
    StrategyPackage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    ReasoningFailureKind as Kind,
)
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    ReasoningProviderFailure,
    ReasoningProviderOutcome,
    ReasoningProviderSuccess,
)
from ai_infra_quant.integrations.openai_reasoning.deepseek_research import normalize_native_memo
from ai_infra_quant.integrations.openai_reasoning.schema import PaqsEReasoningResultSchemaV1


class JsonTransport(Protocol):
    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]: ...


class HttpJsonTransport:
    def post(self, endpoint: str, secret: str, body: dict[str, Any]) -> dict[str, Any]:
        # A new stateless client per request; no SDK debug/body logging or retry middleware.
        with (
            httpx.Client(timeout=120, follow_redirects=False, trust_env=False) as client,
            client.stream(
                "POST", endpoint, headers={"Authorization": "Bearer " + secret}, json=body
            ) as response,
        ):
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > 2_000_000:
                    raise ValueError("Provider response exceeds bound")
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("Invalid provider envelope")
        return value


def _contains_secret(value: object, secret: str) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, dict):
        return any(
            _contains_secret(key, secret) or _contains_secret(item, secret)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret(item, secret) for item in value)
    return False


def _text(response: dict[str, Any], surface: str, *, research: bool = False) -> str:
    if response.get("error") or response.get("status") in {"failed", "incomplete", "cancelled"}:
        raise ValueError("Incomplete provider result")
    if surface == "chat":
        choices = response["choices"]
        if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
            raise ValueError("Incomplete provider result")
        message = choices[0]["message"]
        if message.get("refusal"):
            raise PermissionError("Provider refusal")
        if message.get("tool_calls"):
            raise ValueError("Unexpected tool invocation")
        text = message["content"]
    else:
        texts = []
        for output in response["output"]:
            kind = output.get("type")
            if kind == "reasoning":
                continue  # Never retain reasoning tokens, summaries, or encrypted transcripts.
            if research and kind == "web_search_call":
                continue
            if kind != "message":
                raise ValueError("Unexpected tool invocation")
            for part in output.get("content", []):
                if part.get("type") == "refusal":
                    raise PermissionError("Provider refusal")
                if part.get("type") not in {"output_text", "text"}:
                    raise ValueError("Unexpected content")
                texts.append(part["text"])
        if len(texts) != 1:
            raise ValueError("Expected one final result")
        text = texts[0]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Missing final result")
    return text


class ModelGateway:
    def __init__(
        self,
        registry: ModelRegistry,
        credentials: ModelCredentials,
        transport: JsonTransport | None = None,
        *,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.registry, self.credentials = registry, credentials
        self.transport = transport or HttpJsonTransport()
        self.now = now

    def reason(
        self, *, request: PaqsEReasoningRequestV1, strategy: StrategyPackage, prompt: PromptPackage
    ) -> ReasoningProviderOutcome:
        matches = [
            item
            for item in self.registry.models
            if item.enabled
            and (item.provider_id, item.model_id) == (request.model_provider, request.model_id)
        ]
        if len(matches) != 1 or (
            strategy.strategy_id != request.primary_strategy_id
            or strategy.content_sha256 != request.primary_strategy_content_sha256
            or hashlib.sha256(strategy.content.encode()).hexdigest() != strategy.content_sha256
            or prompt.prompt_version != request.prompt_version
            or prompt.content_sha256 != request.prompt_content_sha256
            or hashlib.sha256(prompt.content.encode()).hexdigest() != prompt.content_sha256
        ):
            return ReasoningProviderFailure(Kind.CONFIGURATION_ERROR, "Runtime identity mismatch")
        model = matches[0]
        secret = self.credentials.secret(model.model_key)
        if not secret:
            return ReasoningProviderFailure(
                Kind.CONFIGURATION_ERROR, "Selected model credential missing"
            )
        instructions = (
            f"{prompt.content}\n\n"
            f"Runtime prompt identity: {prompt.prompt_version} / {prompt.content_sha256}.\n"
            f"Selected primary strategy: {strategy.strategy_id} / {strategy.content_sha256}."
        )
        strategy_input = (
            f"PRIMARY STRATEGY MARKDOWN\nstrategy_id={strategy.strategy_id}\n"
            f"content_sha256={strategy.content_sha256}\n\n{strategy.content}"
        )
        schema = PaqsEReasoningResultSchemaV1.model_json_schema()
        output_format: dict[str, Any] = {
            "type": "json_schema",
            "name": "PaqsEReasoningResultSchemaV1",
            "strict": True,
            "schema": schema,
        }
        body: dict[str, Any] = {"model": model.model_id, "stream": False}
        if model.api_surface == "responses":
            body.update(
                instructions=instructions,
                input=[
                    {"role": "developer", "content": strategy_input},
                    {"role": "user", "content": canonical_json(request)},
                ],
                text={"format": output_format},
                store=False,
                tools=[],
                tool_choice="none",
            )
        else:
            body.update(
                messages=[
                    {
                        "role": "system",
                        "content": instructions + "\nJSON schema: " + json.dumps(schema),
                    },
                    {"role": "user", "content": strategy_input},
                    {"role": "user", "content": canonical_json(request)},
                ],
                response_format={"type": "json_object"},
                tools=[],
                tool_choice="none",
            )
            if model.provider_id == "bigmodel":
                body["thinking"] = {"type": "disabled"}
            if model.structured_output_mode == "json_schema":
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        key: value for key, value in output_format.items() if key != "type"
                    },
                }
            if model.provider_id == "alibaba":
                # Qwen documents JSON Schema on Chat, native source evidence on Responses.
                body.update(enable_search=False, enable_thinking=False)
        try:
            response = self.transport.post(model.endpoint, secret, body)
        except Exception:
            return ReasoningProviderFailure(
                Kind.PROVIDER_UNAVAILABLE, "Selected provider request failed"
            )
        try:
            # The model must never be able to echo a credential into the immutable ledger.
            if _contains_secret(response, secret):
                raise ValueError("Unsafe response")
            if response.get("model", model.model_id) != model.model_id:
                raise ValueError("Provider model mismatch")
            parsed = PaqsEReasoningResultSchemaV1.model_validate_json(
                _text(response, model.api_surface)
            )
            result = parsed.to_domain()
            response_id = response.get("id")
            if response_id is not None and (
                not isinstance(response_id, str) or len(response_id) > 256
            ):
                raise ValueError("Invalid response identity")
            return ReasoningProviderSuccess(result, response_id)
        except PermissionError:
            return ReasoningProviderFailure(
                Kind.PROVIDER_REFUSAL, "Selected provider declined analysis"
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            return ReasoningProviderFailure(
                Kind.INVALID_STRUCTURED_OUTPUT, "Provider output failed strict PAQS-E parsing"
            )

    def research(
        self, model: ModelDescriptor, snapshot: PaqsMarketSnapshot
    ) -> tuple[AuxiliaryContextItem, ...]:
        if (
            model != self.registry.resolve(model.model_key)
            or not model.web_research_supported
            or model.research_endpoint is None
        ):
            raise ResearchFailure(Kind.CONFIGURATION_ERROR)
        secret = self.credentials.secret(model.model_key)
        if not secret:
            raise ResearchFailure(Kind.CONFIGURATION_ERROR)
        intent = (
            f"{snapshot.security.symbol} {snapshot.security.market}: company news, earnings and "
            f"public event context published no later than {snapshot.as_of_timestamp.isoformat()}"
        )
        body: dict[str, Any] = {
            "model": model.model_id,
            "store": False,
            "stream": False,
            "tools": [{"type": "web_search"}],
            "tool_choice": "required",
            "max_output_tokens": 6000,
            "instructions": (
                "Research only the supplied intent with at most four search queries. "
                "Do not analyze "
                'a trade or output chain-of-thought. Return only JSON {"items":[{"url":"...",'
                '"summary":"bounded factual source-specific summary"}]}. At most eight items; '
                "each summary at most 1600 characters. "
                "Each URL must be a native search source. "
                "Keep summaries source-specific. Exclude publications after the cutoff. "
                "Never treat current web prices as Snapshot facts."
            ),
            "input": intent,
        }
        if model.provider_id == "openai":
            body.update(max_tool_calls=4, include=["web_search_call.action.sources"])
        if model.provider_id == "deepseek":
            body["instructions"] = (
                "Research only the supplied Security and Snapshot As-Of intent using at most "
                "four search queries. Return one concise factual research memo, at most 24000 "
                "characters. Do not provide a PAQS-E trading analysis or chain-of-thought. "
                "Exclude sources published after the cutoff. Frozen Snapshot market facts "
                "take precedence; web prices are not authoritative Snapshot facts."
            )
        try:
            response = self.transport.post(model.research_endpoint, secret, body)
        except Exception:
            raise ResearchFailure(Kind.PROVIDER_UNAVAILABLE) from None
        try:
            if _contains_secret(response, secret):
                raise ValueError("Unsafe response")
            if response.get("model", model.model_id) != model.model_id:
                raise ValueError("Model mismatch")
            if model.provider_id == "deepseek":
                return normalize_native_memo(response, model, snapshot, self.now(), intent)
            return normalize_research(response, model, snapshot, self.now(), intent)
        except PermissionError:
            raise ResearchFailure(Kind.PROVIDER_REFUSAL) from None
        except (KeyError, TypeError, ValueError):
            raise ResearchFailure(Kind.INVALID_STRUCTURED_OUTPUT) from None


def normalize_research(
    response: dict[str, Any],
    model: ModelDescriptor,
    snapshot: PaqsMarketSnapshot,
    retrieved_at: datetime,
    intent: str,
) -> tuple[AuxiliaryContextItem, ...]:
    text = _text(response, "responses", research=True)
    calls = [item for item in response["output"] if item.get("type") == "web_search_call"]
    max_actions = 10 if model.provider_id == "deepseek" else 4
    if not 1 <= len(calls) <= max_actions:
        raise ValueError("Research query bound")
    sources: dict[str, dict[str, Any]] = {}
    future_sources: set[str] = set()
    raw_source_count = 0

    def remember(source: dict[str, Any]) -> None:
        nonlocal raw_source_count
        raw_source_count += 1
        if raw_source_count > 64:
            raise ValueError("Research raw source bound")
        published = _publication_time(source)
        if published is not None and published > snapshot.as_of_timestamp:
            future_sources.add(source["url"])
        sources[source["url"]] = {
            **sources.get(source["url"], {}),
            **{key: value for key, value in source.items() if value is not None},
        }

    queries: list[str] = []
    for call in calls:
        if call.get("status") != "completed" or not isinstance(call.get("action"), dict):
            raise ValueError("Incomplete search")
        action = call["action"]
        action_type = action.get("type")
        if model.provider_id == "deepseek" and action_type in {"open_page", "find_in_page"}:
            # Page targets/contents are not source authority. Only native search sources
            # and URL citations below can ground included evidence; never persist traces.
            continue
        if action_type != "search":
            raise ValueError("Unknown search action")
        query = action.get("query")
        values = action.get("queries", [query] if query else [])
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not 0 < len(value) <= 500 for value in values)
        ):
            raise ValueError("Missing query provenance")
        queries.extend(values)
        for source in action.get("sources", []):
            remember(source)
    if not 1 <= len(queries) <= 4 or len(sources) > 64:
        raise ValueError("Research query/source bound")
    # Annotations may add titles/publication metadata to the exact native source URLs.
    for message in response["output"]:
        if message.get("type") == "message":
            for part in message.get("content", []):
                for citation in part.get("annotations", []):
                    if citation.get("type") == "url_citation" and citation.get("url"):
                        remember(citation)
    if not sources or len(sources) > 64:
        raise ValueError("Research source bound")
    summaries = json.loads(text)
    if (
        set(summaries) != {"items"}
        or not isinstance(summaries["items"], list)
        or not 1 <= len(summaries["items"]) <= 8
    ):
        raise ValueError("Research item bound")
    items: list[AuxiliaryContextItem] = []
    seen: set[str] = set()
    for summary in summaries["items"]:
        if set(summary) != {"url", "summary"}:
            raise ValueError("Unexpected evidence fields")
        url, content = summary["url"], summary["summary"]
        if not isinstance(url, str) or url not in sources or url in seen or len(url) > 1000:
            raise ValueError("Unverified source")
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"https", "http"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("Invalid source URL")
        seen.add(url)
        if not isinstance(content, str) or not 0 < len(content.strip()) <= 1600:
            raise ValueError("Research content bound")
        source = sources[url]
        published = _publication_time(source)
        if url in future_sources:
            continue
        title = source.get("title") or url
        if not isinstance(title, str) or len(title) > 500:
            raise ValueError("Source title bound")
        provenance = json.dumps(
            {
                "url": url,
                "provider": model.provider_id,
                "model": model.model_id,
                "retrieved_at": retrieved_at.isoformat(),
                "queries": queries,
                "intent": intent,
                "publication_time": published.isoformat() if published else "unknown",
                "limitation": (
                    "Source-specific model summary; Snapshot market facts take precedence."
                    + (
                        " Publication time unknown; cutoff compatibility "
                        "cannot be independently confirmed."
                        if published is None
                        else ""
                    )
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        if len(content) + len(provenance) + len(title) > 4000:
            raise ValueError("Normalized item bound")
        context_id = "web-" + hashlib.sha256((url + "\n" + content).encode()).hexdigest()[:24]
        items.append(
            AuxiliaryContextItem(
                context_id, "web_research", title, published, provenance, True, content
            )
        )
    if (
        not items
        or sum(
            len(item.content) + len(item.provenance or "") + len(item.source_label)
            for item in items
        )
        > 24000
    ):
        raise ValueError("No compatible evidence or total bound exceeded")
    return tuple(items)


def _publication_time(source: dict[str, Any]) -> datetime | None:
    times = []
    for field in ("published_at", "publication_date"):
        timestamp = source.get(field)
        if timestamp is None:
            continue
        if not isinstance(timestamp, str):
            raise ValueError("Invalid source timestamp")
        published = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if published.tzinfo is None:
            raise ValueError("Source timestamp lacks timezone")
        times.append(published.astimezone(UTC))
    return max(times) if times else None

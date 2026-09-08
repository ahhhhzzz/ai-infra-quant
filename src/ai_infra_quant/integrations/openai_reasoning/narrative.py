"""Plain final-text gateway, separate from legacy PAQS-E structured output."""

from __future__ import annotations

from typing import Any

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.core.domain.paqs_e_ledger import payload_sha256
from ai_infra_quant.core.domain.paqs_e_narrative import (
    NarrativeFailure,
    NarrativeRequest,
    NarrativeSuccess,
)
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeFailureKind as Kind
from ai_infra_quant.core.domain.paqs_e_reasoning import PromptPackage, StrategyPackage
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.integrations.openai_reasoning.gateway import (
    HttpJsonTransport,
    JsonTransport,
    _contains_secret,
    _text,
)


class NarrativeGateway:
    def __init__(
        self,
        registry: ModelRegistry,
        credentials: ModelCredentials,
        transport: JsonTransport | None = None,
    ) -> None:
        self.registry, self.credentials = registry, credentials
        self.transport = transport or HttpJsonTransport()

    def reason_text(
        self, *, request: NarrativeRequest, strategy: StrategyPackage, prompt: PromptPackage
    ) -> NarrativeSuccess | NarrativeFailure:
        matches = [
            model
            for model in self.registry.models
            if model.enabled
            and (model.provider_id, model.model_id) == (request.model_provider, request.model_id)
        ]
        if (
            len(matches) != 1
            or (
                strategy.strategy_id,
                strategy.content_sha256,
                prompt.prompt_version,
                prompt.content_sha256,
            )
            != (
                request.primary_strategy_id,
                request.primary_strategy_content_sha256,
                request.prompt_version,
                request.prompt_content_sha256,
            )
            or payload_sha256(strategy.content) != strategy.content_sha256
            or payload_sha256(prompt.content) != prompt.content_sha256
        ):
            return NarrativeFailure(Kind.CONFIGURATION_ERROR)
        model = matches[0]
        secret = self.credentials.secret(model.model_key)
        if not secret:
            return NarrativeFailure(Kind.CONFIGURATION_ERROR)
        body: dict[str, Any] = {
            "model": model.model_id,
            "stream": False,
            "tools": [],
            "tool_choice": "none",
        }
        if model.api_surface == "responses":
            body.update(
                instructions=prompt.content,
                input=[
                    {"role": "developer", "content": strategy.content},
                    {"role": "user", "content": canonical_json(request)},
                ],
                store=False,
            )
        else:
            body["messages"] = [
                {"role": "system", "content": prompt.content},
                {"role": "user", "content": strategy.content},
                {"role": "user", "content": canonical_json(request)},
            ]
            if model.provider_id == "alibaba":
                body.update(enable_search=False, enable_thinking=False)
            if model.provider_id == "bigmodel":
                body["thinking"] = {"type": "disabled"}
        try:
            response = self.transport.post(model.endpoint, secret, body)
        except Exception:
            return NarrativeFailure(Kind.PROVIDER_UNAVAILABLE)
        try:
            if (
                _contains_secret(response, secret)
                or response.get("model", model.model_id) != model.model_id
            ):
                return NarrativeFailure(Kind.INVALID_FINAL_TEXT)
            if response.get("status") in {"incomplete", "cancelled", "in_progress", "queued"}:
                return NarrativeFailure(Kind.PROVIDER_INCOMPLETE)
            if response.get("error") or response.get("status") == "failed":
                return NarrativeFailure(Kind.PROVIDER_UNAVAILABLE)
            if model.api_surface == "chat":
                choices = response["choices"]
                if len(choices) == 1 and choices[0].get("finish_reason") in {"length", None}:
                    return NarrativeFailure(Kind.PROVIDER_INCOMPLETE)
                if len(choices) == 1:
                    if choices[0].get("finish_reason") == "content_filter":
                        return NarrativeFailure(Kind.PROVIDER_REFUSAL)
                    if choices[0]["message"].get("role", "assistant") != "assistant":
                        return NarrativeFailure(Kind.INVALID_FINAL_TEXT)
            else:
                if response.get("status") != "completed":
                    return NarrativeFailure(Kind.INVALID_FINAL_TEXT)
                if any(
                    item.get("type") == "message" and item.get("role", "assistant") != "assistant"
                    for item in response["output"]
                ):
                    return NarrativeFailure(Kind.INVALID_FINAL_TEXT)
                if any(
                    item.get("status") in {"incomplete", "in_progress", "cancelled"}
                    for item in response["output"]
                ):
                    return NarrativeFailure(Kind.PROVIDER_INCOMPLETE)
            return NarrativeSuccess(_text(response, model.api_surface), response.get("id"))
        except PermissionError:
            return NarrativeFailure(Kind.PROVIDER_REFUSAL)
        except (ValueError, TypeError, KeyError, AttributeError):
            return NarrativeFailure(Kind.INVALID_FINAL_TEXT)

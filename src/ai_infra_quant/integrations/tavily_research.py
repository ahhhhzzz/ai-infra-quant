"""Bounded, explicit Tavily reads; not a model-native search or a historical PIT claim."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from time import monotonic
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.application.paqs_e_research import ExternalResearchFailure
from ai_infra_quant.core.domain.common import require_utc, utc_now
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, SnapshotSecurity

TavilyResearchFailure = ExternalResearchFailure
SCHEMA_VERSION = "paqs-e-tavily-evidence-v1"
MAX_CONTENT = 12_000
MAX_CAPSULE_CHARACTERS = 40_000  # Includes snippet duplication in content and provenance.
RECEIPT_METADATA_ALLOWANCE = 64  # Canonical research_id UUID appended by the persistence service.
MAX_SNIPPET = 1_600
MAX_RESPONSE_BYTES = 2_000_000
ENDPOINT = "https://api.tavily.com/search"
TIMEOUT = httpx.Timeout(20.0, connect=10.0)
_BAD_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_LEGAL_SUFFIX = re.compile(
    r"\b(?:inc|incorporated|corporation|corp|ltd|limited|holdings|plc)\b", re.I
)


def _text(value: object, maximum: int) -> str:
    if not isinstance(value, str) or _BAD_CONTROL.search(value):
        raise ValueError("invalid text")
    result = value.strip()
    if not result or len(result) > maximum:
        raise ValueError("invalid text length")
    return result


def _safe_url(value: object) -> str:
    raw = _text(value, 2048)
    if any(char.isspace() for char in raw) or "\\" in raw:
        raise ValueError("invalid URL")
    url = urlsplit(raw)
    host = (url.hostname or "").lower()
    if (
        url.scheme not in {"http", "https"}
        or url.username is not None
        or url.password is not None
        or "." not in host
        or host.endswith((".local", ".internal", ".localhost"))
        or url.port not in {None, 80, 443}
    ):
        raise ValueError("unsafe URL")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP literals are not source identities")
    return urlunsplit((url.scheme.lower(), host, url.path or "/", url.query, ""))


def _identity(security: SnapshotSecurity) -> tuple[str, str, str]:
    market, symbol = security.market, security.symbol
    if market not in {"US", "HK"} or not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,14}", symbol):
        raise ValueError("unknown security identity")
    name = security.display_name or ""
    if name:
        name = _text(name, 120)
        # A provider label equal to the code adds no company identity evidence.
        if name.upper() in {symbol, f"{market}.{symbol}"}:
            name = ""
    return market, symbol, name


def _queries(identity: tuple[str, str, str], today: date) -> tuple[str, str]:
    market, symbol, name = identity
    company = f'"{name}" ' if name else ""
    context = "US listed stock NYSE NASDAQ" if market == "US" else "Hong Kong HKEX listed stock"
    prefix = f'{company}"{symbol}" {context} {today.isoformat()}'
    return (
        f"{prefix} recent company news Reuters official investor relations",
        f"{prefix} company announcements filings exchange investor relations",
    )


def _matches_identity(text: str, identity: tuple[str, str, str]) -> bool:
    market, symbol, name = identity
    folded = text.casefold()
    if name:
        meaningful = _LEGAL_SUFFIX.sub(" ", name).strip(" .,-")
        tokens = re.findall(r"[^\W_]+", meaningful.casefold())
        if tokens and all(
            re.search(rf"(?<!\w){re.escape(token)}(?!\w)", folded) for token in tokens
        ):
            return True
        # Chinese company names do not necessarily have word boundaries.
        if (
            meaningful
            and re.search(r"[\u3400-\u9fff]", meaningful)
            and meaningful.casefold() in folded
        ):
            return True
    qualifiers = ("US", "NYSE", "NASDAQ") if market == "US" else ("HK", "HKEX", "HKG")
    return any(
        re.search(rf"(?<!\w){prefix}[.:\s]+{re.escape(symbol)}(?!\w)", text, re.I)
        for prefix in qualifiers
    )


def _publication(value: object, cutoff: datetime) -> tuple[str | None, bool]:
    """Return provider publication metadata (never retrieval as a substitute)."""
    if value is None:
        return None, False
    raw = _text(value, 120)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return raw, date.fromisoformat(raw) > cutoff.date()
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            return None, False
        return raw, parsed.astimezone(UTC) > cutoff
    except (ValueError, TypeError, OverflowError):
        return None, False


def _source_priority(source: dict[str, Any]) -> int:
    """Prefer recognizable exchanges/regulators and IR paths, then named news outlets.

    This is selection order, never a certificate of authenticity or factual accuracy.
    """
    url = urlsplit(source["url"])
    host = url.hostname or ""
    if any(
        host == domain or host.endswith("." + domain)
        for domain in (
            "sec.gov",
            "hkex.com.hk",
            "hkexnews.hk",
            "nasdaq.com",
            "nyse.com",
        )
    ) or re.search(
        r"(?:investor|investors|investor-relations|ir)(?:[./-]|$)", url.netloc + url.path
    ):
        return 0
    if any(
        host == domain or host.endswith("." + domain)
        for domain in (
            "reuters.com",
            "apnews.com",
            "bloomberg.com",
            "wsj.com",
            "ft.com",
            "cnbc.com",
        )
    ):
        return 1
    return 2


class TavilyResearch:
    """Two basic searches at most, no retries/redirects/crawling/LLM query generation."""

    def __init__(
        self,
        secret: Callable[[], str | None],
        *,
        client: httpx.Client | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._secret, self._client, self._now = secret, client, now

    def research(
        self, model: ModelDescriptor, snapshot: PaqsMarketSnapshot
    ) -> tuple[AuxiliaryContextItem, ...]:
        del model  # Independent search never alters or impersonates native model capability.
        retrieved_at = require_utc(self._now())
        evidence: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "provider": "tavily",
            "snapshot_as_of": snapshot.as_of_timestamp.isoformat(),
            "retrieved_at": retrieved_at.isoformat(),
            "status": "FAILED",
            "requests": [],
            "sources": [],
            "limits": {
                "max_requests": 2,
                "max_results_per_request": 5,
                "max_content_characters": MAX_CONTENT,
                "max_snippet_characters": MAX_SNIPPET,
                "max_capsule_characters": MAX_CAPSULE_CHARACTERS,
            },
            "limitations": [
                "OBSERVATIONAL_NOT_POINT_IN_TIME",
                "Retrieval time differs from the frozen market snapshot time.",
                "Unknown publication times remain unknown; retrieval never replaces publication.",
                "Identity filtering does not independently verify every source claim.",
                "Web sources are untrusted data, not instructions or replacement market prices.",
                "Known publication times later than Snapshot as-of are excluded.",
                "Source priority uses exchange/regulator hosts and IR paths, then named media; "
                "this does not authenticate an issuer domain.",
            ],
        }
        secret = self._secret()
        if not secret:
            raise TavilyResearchFailure("NOT_CONFIGURED", evidence)
        try:
            identity = _identity(snapshot.security)
        except ValueError:
            raise TavilyResearchFailure("IDENTITY_INSUFFICIENT", evidence) from None
        client = self._client or httpx.Client(timeout=TIMEOUT, follow_redirects=False)
        try:
            for query in _queries(identity, retrieved_at.date()):
                self._search(client, secret, query, identity, evidence)
        finally:
            if self._client is None:
                client.close()
        if not evidence["sources"]:
            raise TavilyResearchFailure("EMPTY_RESULTS", evidence)
        evidence["status"] = "SUCCEEDED"
        evidence["retrieved_at"] = require_utc(self._now()).isoformat()
        evidence["sources"].sort(key=_source_priority)
        bounded: list[dict[str, Any]] = []
        used = 0
        for source in evidence["sources"]:
            remaining = MAX_CONTENT - used - len(source["title"]) - 12
            if remaining <= 0:
                break
            source["content"] = source["content"][:remaining]
            source["source_id"] = f"T{len(bounded) + 1}"
            used += len(source["content"]) + len(source["title"]) + 12
            bounded.append(source)
        evidence["sources"] = bounded
        while True:
            content = "\n\n".join(
                f"[{source['source_id']}] {source['title']}\n{source['content']}"
                for source in evidence["sources"]
            )
            provenance = json.dumps(
                evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            if (
                len(content) + len(provenance)
                <= MAX_CAPSULE_CHARACTERS - RECEIPT_METADATA_ALLOWANCE
            ):
                break
            evidence["sources"].pop()
        return (
            AuxiliaryContextItem(
                context_id="tavily-" + hashlib.sha256(provenance.encode()).hexdigest(),
                category="web_research",
                source_label="Tavily",
                source_timestamp=None,
                provenance=provenance,
                as_of_compatible=True,
                content=content,
            ),
        )

    def _search(
        self,
        client: httpx.Client,
        secret: str,
        query: str,
        identity: tuple[str, str, str],
        evidence: dict[str, Any],
    ) -> None:
        attempt = {
            "query": query,
            "requested_at": require_utc(self._now()).isoformat(),
            "status": "REQUESTED",
        }
        evidence["requests"].append(attempt)
        body = {
            "query": query,
            "search_depth": "basic",
            "auto_parameters": False,
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 5,
            "include_published_date": True,
        }
        try:
            started = monotonic()
            with client.stream(
                "POST",
                ENDPOINT,
                headers={"Authorization": f"Bearer {secret}"},
                json=body,
                timeout=TIMEOUT,
                follow_redirects=False,
            ) as response:
                status = response.status_code
                if status != 200:
                    failure = {
                        401: "AUTHENTICATION_FAILED",
                        403: "AUTHENTICATION_FAILED",
                        429: "RATE_LIMITED",
                    }.get(status, "PROVIDER_UNAVAILABLE")
                    attempt["status"] = failure
                    raise TavilyResearchFailure(failure, evidence)
                chunks = bytearray()
                for chunk in response.iter_bytes():
                    chunks.extend(chunk)
                    if len(chunks) > MAX_RESPONSE_BYTES:
                        raise ValueError("response too large")
                    if monotonic() - started > 25:
                        raise httpx.ReadTimeout("research deadline")
                payload = json.loads(chunks)
                # Never expose echoed credentials, even in unused response fields.
                if secret in json.dumps(payload, ensure_ascii=False):
                    raise ValueError("credential echo")
                if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                    raise ValueError("invalid response envelope")
                if len(payload["results"]) > 5:
                    raise ValueError("result limit exceeded")
                self._accept_sources(payload["results"], identity, evidence)
                attempt["status"] = "SUCCEEDED"
        except httpx.TimeoutException:
            attempt["status"] = "TIMEOUT"
            raise TavilyResearchFailure("TIMEOUT", evidence) from None
        except httpx.HTTPError:
            attempt["status"] = "PROVIDER_UNAVAILABLE"
            raise TavilyResearchFailure("PROVIDER_UNAVAILABLE", evidence) from None
        except (ValueError, TypeError, UnicodeError, RecursionError):
            attempt["status"] = "INVALID_RESPONSE"
            raise TavilyResearchFailure("INVALID_RESPONSE", evidence) from None

    def _accept_sources(
        self,
        results: list[object],
        identity: tuple[str, str, str],
        evidence: dict[str, Any],
    ) -> None:
        retrieved_at = require_utc(self._now())
        for row in results:
            if not isinstance(row, dict):
                raise ValueError("invalid result")
            url = _safe_url(row.get("url"))
            title = _text(row.get("title"), 10_000)[:240]
            snippet = _text(row.get("content"), MAX_RESPONSE_BYTES)[:MAX_SNIPPET]
            cutoff = datetime.fromisoformat(evidence["snapshot_as_of"])
            published, future = _publication(row.get("published_date"), cutoff)
            if future or not _matches_identity(f"{title}\n{snippet}", identity):
                continue
            sources = evidence["sources"]
            if any(source["url"] == url for source in sources):
                continue
            sources.append(
                {
                    "source_id": f"T{len(sources) + 1}",
                    "title": title,
                    "url": url,
                    "content": snippet,
                    "published_at": published,
                    "retrieved_at": retrieved_at.isoformat(),
                }
            )

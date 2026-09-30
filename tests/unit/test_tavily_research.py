"""Synthetic HTTP evidence only; never a paid Tavily or model call."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from test_paqs_e_runtime import _snapshot

from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json
from ai_infra_quant.integrations.tavily_research import (
    MAX_CAPSULE_CHARACTERS,
    MAX_CONTENT,
    MAX_RESPONSE_BYTES,
    MAX_SNIPPET,
    TavilyResearch,
    TavilyResearchFailure,
)

MODEL = ModelRegistry().resolve("deepseek-flash")
NOW = datetime(2026, 9, 30, 12, tzinfo=UTC)
SECRET = "synthetic-search-key-not-real"


def snapshot_with_name(name: str | None) -> PaqsMarketSnapshot:
    snapshot = _snapshot()
    security = replace(snapshot.security, display_name=name)
    payload = {**snapshot.canonical_hash_payload(), "security": security}
    digest = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
    return replace(snapshot, security=security, snapshot_hash=digest)


def source(index: int = 1, **overrides: Any) -> dict[str, Any]:
    return {
        "title": "Broadcom company announcement",
        "url": f"https://example.org/{index}",
        "content": "Broadcom released a company statement. Synthetic fixture.",
        **overrides,
    }


class SearchFixture:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []
        self.headers: list[httpx.Headers] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.tavily.com/search"
        self.calls.append(json.loads(request.content))
        self.headers.append(request.headers)
        result = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        if isinstance(result, Exception):
            raise result
        if isinstance(result, httpx.Response):
            return result
        return httpx.Response(200, json=result)

    def adapter(self, secret: str | None = SECRET) -> TavilyResearch:
        return TavilyResearch(
            lambda: secret,
            now=lambda: NOW,
            client=httpx.Client(transport=httpx.MockTransport(self.handle)),
        )


def test_basic_queries_bounds_provenance_dedup_and_no_native_impersonation() -> None:
    fixture = SearchFixture(
        [
            {"results": [source(published_date="2026-09-03")]},
            {"results": [source(url="https://EXAMPLE.org/1#fragment"), source(2)]},
        ]
    )
    (item,) = fixture.adapter().research(MODEL, _snapshot())
    evidence = json.loads(item.provenance or "")
    assert len(fixture.calls) == 2
    assert [s["source_id"] for s in evidence["sources"]] == ["T1", "T2"]
    assert evidence["sources"][0]["published_at"] == "2026-09-03"
    assert evidence["sources"][1]["published_at"] is None
    assert evidence["sources"][0]["content"] in item.content
    assert item.source_timestamp is None and item.source_label == "Tavily"
    assert evidence["schema_version"] == "paqs-e-tavily-evidence-v1"
    assert "OBSERVATIONAL_NOT_POINT_IN_TIME" in evidence["limitations"]
    assert evidence["snapshot_as_of"] != evidence["retrieved_at"]
    assert "web_search_call" not in (item.provenance or "")
    assert not MODEL.web_research_supported  # Real native capability remains disabled.
    for body, headers in zip(fixture.calls, fixture.headers, strict=True):
        assert headers["Authorization"] == f"Bearer {SECRET}"
        assert body["search_depth"] == "basic" and body["max_results"] == 5
        assert not body["auto_parameters"] and not body["include_answer"]
        assert not body["include_raw_content"] and body["include_published_date"]
        assert all(
            part in body["query"]
            for part in (
                '"Broadcom"',
                '"AVGO"',
                "US listed stock NYSE NASDAQ",
                "2026-09-30",
            )
        )
        assert '"US.AVGO"' not in body["query"]
        assert len(body["query"]) < 400
        assert "snapshot_hash" not in body and "security_id" not in body
    assert SECRET not in str(evidence) and SECRET not in item.content


def test_content_is_bounded_and_sources_are_actual_truncated_model_snippets() -> None:
    fixture = SearchFixture(
        [
            {"results": [source(i, content="Broadcom " + "x" * 9000) for i in range(5)]},
            {"results": [source(i, content="Broadcom " + "y" * 9000) for i in range(5, 10)]},
        ]
    )
    (item,) = fixture.adapter().research(MODEL, _snapshot())
    evidence = json.loads(item.provenance or "")
    assert len(item.content) <= MAX_CONTENT
    assert len(item.content) + len(item.provenance or "") <= MAX_CAPSULE_CHARACTERS
    assert 5 < len(evidence["sources"]) <= 10
    for included in evidence["sources"]:
        assert 0 < len(included["content"]) <= MAX_SNIPPET
        assert included["content"] in item.content


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "AUTHENTICATION_FAILED"),
        (403, "AUTHENTICATION_FAILED"),
        (429, "RATE_LIMITED"),
        (503, "PROVIDER_UNAVAILABLE"),
        (302, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_status_failures_are_safe_and_not_retried(status: int, code: str) -> None:
    fixture = SearchFixture([httpx.Response(status, text=f"unsafe upstream body {SECRET}")])
    with pytest.raises(TavilyResearchFailure) as failed:
        fixture.adapter().research(MODEL, _snapshot())
    assert failed.value.failure_code == code
    assert len(fixture.calls) == 1
    assert SECRET not in str(failed.value) + str(failed.value.evidence)
    assert failed.value.evidence["requests"][0]["status"] == code


def test_timeout_empty_missing_key_and_second_request_failure() -> None:
    for response, code in [
        (httpx.ReadTimeout("secret exception must not escape"), "TIMEOUT"),
        ({"results": []}, "EMPTY_RESULTS"),
    ]:
        fixture = SearchFixture([response])
        with pytest.raises(TavilyResearchFailure) as failed:
            fixture.adapter().research(MODEL, _snapshot())
        assert failed.value.failure_code == code
        assert len(fixture.calls) == (2 if code == "EMPTY_RESULTS" else 1)
    fixture = SearchFixture([{"results": [source()]}])
    with pytest.raises(TavilyResearchFailure, match="research") as failed:
        fixture.adapter(None).research(MODEL, _snapshot())
    assert failed.value.failure_code == "NOT_CONFIGURED" and fixture.calls == []
    fixture = SearchFixture([{"results": [source()]}, httpx.Response(429)])
    with pytest.raises(TavilyResearchFailure) as failed:
        fixture.adapter().research(MODEL, _snapshot())
    assert failed.value.failure_code == "RATE_LIMITED" and len(fixture.calls) == 2
    assert failed.value.evidence["status"] == "FAILED"


@pytest.mark.parametrize(
    "response",
    [
        {"results": "wrong"},
        {"results": [None]},
        {"answer": "text is not search evidence"},
        {"results": [source()] * 6},
        {"results": [source(content=None)]},
        {"results": [source(url="http://127.0.0.1/source")]},
        {"results": [source(url="https://user:pass@example.org/a")]},
        {"results": [source(url="javascript:alert(1)")]},
        {"results": [source(url="https://service.local/a")]},
        {"results": [source()], "unused": SECRET},
        {"results": [source(title=SECRET)]},
    ],
)
def test_bad_envelopes_and_secret_echo_fail_closed(response: object) -> None:
    fixture = SearchFixture([response])
    with pytest.raises(TavilyResearchFailure) as failed:
        fixture.adapter().research(MODEL, _snapshot())
    assert failed.value.failure_code == "INVALID_RESPONSE"
    assert len(fixture.calls) == 1 and SECRET not in str(failed.value.evidence)


def test_oversized_body_and_invalid_json_are_rejected_without_capture() -> None:
    for body in (b"{" + b" " * MAX_RESPONSE_BYTES, b"not JSON"):
        fixture = SearchFixture([httpx.Response(200, content=body)])
        with pytest.raises(TavilyResearchFailure) as failed:
            fixture.adapter().research(MODEL, _snapshot())
        assert failed.value.failure_code == "INVALID_RESPONSE"
        assert len(fixture.calls) == 1


def test_short_ticker_collision_future_and_unknown_publication_handling() -> None:
    snapshot = snapshot_with_name(None)
    fixture = SearchFixture(
        [
            {
                "results": [
                    source(
                        title="AVGO other company",
                        content="The code AVGO alone is not identity evidence.",
                    ),
                    source(
                        2,
                        title="NASDAQ:AVGO announcement",
                        content="Listed company notice.",
                        published_date="2026-10-01",
                    ),
                    source(
                        3,
                        title="NASDAQ:AVGO announcement",
                        content="Listed company notice.",
                        published_date="not-a-date",
                    ),
                ]
            }
        ]
    )
    (item,) = fixture.adapter().research(MODEL, snapshot)
    sources = json.loads(item.provenance or "")["sources"]
    assert len(sources) == 1 and sources[0]["url"].endswith("/3")
    assert sources[0]["published_at"] is None


def test_company_name_disambiguation_and_invalid_input_make_no_search() -> None:
    fixture = SearchFixture(
        [
            {
                "results": [
                    source(
                        title="Virtual training AVGO company",
                        content="Different company unrelated to issuer",
                    )
                ]
            }
        ]
    )
    with pytest.raises(TavilyResearchFailure) as failed:
        fixture.adapter().research(MODEL, _snapshot())
    assert failed.value.failure_code == "EMPTY_RESULTS"
    snapshot = snapshot_with_name("x" * 121)
    fixture = SearchFixture([{"results": [source()]}])
    with pytest.raises(TavilyResearchFailure) as failed:
        fixture.adapter().research(MODEL, snapshot)
    assert failed.value.failure_code == "IDENTITY_INSUFFICIENT" and fixture.calls == []


def test_capsule_overhead_is_bounded_and_credible_sources_are_selected_first() -> None:
    long_path = "a" * 1950
    rows = [
        source(i, url=f"https://example.org/{i}/{long_path}", content="Broadcom " + "z" * 5000)
        for i in range(8)
    ]
    rows += [
        source(8, url="https://reuters.com/article/broadcom"),
        source(9, url="https://investors.broadcom.com/news/announcement"),
    ]
    fixture = SearchFixture([{"results": rows[:5]}, {"results": rows[5:]}])
    (item,) = fixture.adapter().research(MODEL, _snapshot())
    evidence = json.loads(item.provenance or "")
    assert len(item.content) + len(item.provenance or "") <= MAX_CAPSULE_CHARACTERS
    assert evidence["sources"][0]["url"].startswith("https://investors.broadcom.com/")
    assert evidence["sources"][1]["url"].startswith("https://reuters.com/")
    assert evidence["sources"][0]["source_id"] == "T1"


def test_known_publication_after_snapshot_is_excluded_even_before_retrieval() -> None:
    fixture = SearchFixture(
        [
            {
                "results": [
                    source(published_date="2026-09-29"),
                    source(2, published_date="2026-09-03T00:00:00Z"),
                ]
            }
        ]
    )
    (item,) = fixture.adapter().research(MODEL, _snapshot())
    sources = json.loads(item.provenance or "")["sources"]
    assert len(sources) == 1 and sources[0]["url"].endswith("/2")


def test_near_limit_capsule_reserves_persisted_receipt_uuid() -> None:
    # These individually valid fields previously left only 21 characters of the
    # combined budget. Appending the real-sized receipt field then exceeded it.
    rows = [
        source(
            i,
            url=f"https://example.org/{i}/" + "a" * 1980,
            title="Broadcom " + "t" * 200,
            content="Broadcom " + "z" * 5000,
        )
        for i in range(10)
    ]
    fixture = SearchFixture([{"results": rows[:5]}, {"results": rows[5:]}])
    (item,) = fixture.adapter().research(MODEL, _snapshot())
    evidence = json.loads(item.provenance or "")
    evidence["research_id"] = "00000000-0000-4000-8000-000000000001"
    persisted_provenance = json.dumps(
        evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert len(item.content) + len(persisted_provenance) <= MAX_CAPSULE_CHARACTERS
    assert len(fixture.calls) == 2

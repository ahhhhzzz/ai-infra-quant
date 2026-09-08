"""Synthetic intercepted network evidence only; never loaded by production code."""
# ruff: noqa: RUF001 -- Chinese prose intentionally retains full-width punctuation.

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Browser, Page, Route

from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.application.paqs_e_runtime import build_reasoning_request, load_strategy_package
from ai_infra_quant.backend.schemas.paqs_e import AnalysisRunRead, DecisionRead
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json

US = "00000000-0000-4000-8000-000000000007"
HK = "00000000-0000-4000-8000-000000000008"
MODEL = "gpt-5.6-luna"
MODEL_NAME = "GPT-5.6 Luna"
STRATEGY = "paqs-e-master"


def fixture_pair(
    revision: int = 1, *, market: str = "US", strategy: str = STRATEGY
) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime_fixtures = importlib.import_module("tests.unit.test_paqs_e_runtime")
    request = build_reasoning_request(snapshot=runtime_fixtures._snapshot(), model_id=MODEL)
    payload = json.loads(canonical_json(request))
    result = json.loads(canonical_json(runtime_fixtures._result(request)))
    snapshot = payload["market_snapshot"]
    security_id = US if market == "US" else HK
    symbol = "AVGO" if market == "US" else "00700"
    zone = "America/New_York" if market == "US" else "Asia/Hong_Kong"
    snapshot["security"].update(
        security_id=security_id,
        market=market,
        symbol=symbol,
        display_symbol=f"{market}.{symbol}",
        currency="USD" if market == "US" else "HKD",
        market_timezone=zone,
    )
    for name, step in (
        ("w1_bars", timedelta(days=7)),
        ("d1_bars", timedelta(days=1)),
        ("m30_bars", timedelta(minutes=30)),
    ):
        template = snapshot[name][0]
        bars = []
        for index in range(80):
            bar = copy.deepcopy(template)
            close = (
                Decimal(90) + Decimal(index) / Decimal(5) + Decimal((index % 7) - 3) / Decimal(2)
            )
            bar.update(
                open=str(close - 1),
                high=str(close + 2),
                low=str(close - 2),
                close=str(close),
                volume=str(1000 + index * 23),
            )
            end = datetime(2026, 9, 3, 20, tzinfo=UTC) - step * (79 - index)
            if name == "d1_bars":
                bar["session_date"] = end.date().isoformat()
            else:
                bar.update(
                    interval_start=(end - step).isoformat(),
                    interval_end=end.isoformat(),
                    market_timezone=zone,
                )
            bars.append(bar)
        snapshot[name] = bars
    # An accepted completed W1 can have a nominal future end, preserved by the UI.
    snapshot["w1_bars"][-1]["interval_end"] = "2026-09-07T00:00:00+00:00"
    for evidence in snapshot["timeframe_evidence_status"].values():
        evidence["authoritative_bar_count"] = 80
    snapshot["source_coverage"].update(
        d1_source_count=400, w1_completed_count=80, minute_source_count=2400, m30_completed_count=80
    )
    snapshot["warnings"] = ["合成浏览器验收夹具；不代表真实行情或策略质量"]
    factual = {
        key: value for key, value in snapshot.items() if key not in {"snapshot_hash", "created_at"}
    }
    snapshot["snapshot_hash"] = hashlib.sha256(canonical_json(factual).encode()).hexdigest()
    for identity in (payload, result["identity"]):
        identity.update(
            market=market,
            symbol=symbol,
            primary_strategy_id=strategy,
            snapshot_hash=snapshot["snapshot_hash"],
        )
    result.update(
        one_line_thesis="合成验收：多周期仍待确认，等待完成的触发 K 线。",
        explanation="仅用于浏览器验收，不代表真实分析。",
    )
    result["context"].update(
        regime_summary="区间整理，方向证据尚不一致。", trend_quality="需要更多完成 K 线确认。"
    )
    for key in ("htf", "stf", "ttf"):
        result["context"][key]["evidence"] = "合成区间证据；尚无明确突破。"
    result["entry"]["wait_condition"] = "等待触发 K 线完成，再确认后续延续。"
    result["key_levels"][0].update(
        price_or_zone="98.123456789012345678–102.987654321098765432 区域；3 次触碰",
        role="候选结构区",
        rationale="完成 K 线的合成结构",
        state_change="接受于区域上方后复核",
    )
    result["invalidation"]["calculation_reference"] = "88.123456789012345678"
    result["targets"]["t1_calculation_reference"] = "125.987654321098765432"
    run_id = f"10000000-0000-4000-8000-{revision:012d}"
    decision_id = f"20000000-0000-4000-8000-{revision:012d}"
    identity = {
        key: value for key, value in result["identity"].items() if not key.startswith("primary_")
    }
    identity.update(
        security_id=security_id,
        strategy_id=strategy,
        strategy_content_sha256=payload["primary_strategy_content_sha256"],
        strategy_artifact_id="30000000-0000-4000-8000-000000000001",
        prompt_artifact_id="30000000-0000-4000-8000-000000000002",
        validator_version="paqs-e-validator-v1",
        created_at=f"2026-09-04T12:{revision:02d}:00+00:00",
    )
    run = {
        **identity,
        "analysis_run_id": run_id,
        "status": "SUCCEEDED",
        "request_payload_json": canonical_json(payload),
        "request_payload_sha256": hashlib.sha256(canonical_json(payload).encode()).hexdigest(),
        "provider_response_id": "synthetic-response",
        "failure_kind": None,
        "failure_reason": None,
        "validation_issues": [],
        "started_at": identity["created_at"],
        "completed_at": identity["created_at"],
    }
    decision = {
        **identity,
        "decision_id": decision_id,
        "analysis_run_id": run_id,
        "revision_no": revision,
        "supersedes_decision_id": f"20000000-0000-4000-8000-{revision - 1:012d}"
        if revision > 1
        else None,
        "result": result,
        "result_payload_sha256": hashlib.sha256(canonical_json(result).encode()).hexdigest(),
        "one_line_thesis": result["one_line_thesis"],
        "entry_advisory": result["entry"]["advisory"],
        "holder_advisory_basis": result["holder"]["advisory_basis"],
        "holder_advisory": result["holder"]["advisory"],
        "market_bias": result["context"]["market_bias"],
        "setup_family": result["setup"]["family"],
        "setup_direction": result["setup"]["direction"],
        "setup_stage": result["setup"]["stage"],
        "rr_status": result["risk_reward"]["rr_status"],
        "rr_t1": result["risk_reward"]["rr_t1"],
        "uncertainty_level": result["uncertainty"]["level"],
    }
    # Verify accepted public schemas; model judgment here is intentionally synthetic.
    AnalysisRunRead.model_validate(run)
    DecisionRead.model_validate(decision)
    return decision, run


def narrative_pair(
    revision: int = 1,
    *,
    market: str = "US",
    strategy: str = STRATEGY,
    prose: str = "  # 最终分析\n合成叙述：等待触发与延续分别确认。{自由文本}\n",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Independent synthetic final text plus the existing factual chart fixture."""
    legacy, old_run = fixture_pair(revision, market=market, strategy=strategy)
    from ai_infra_quant.application.paqs_e_narrative import load_narrative_prompt

    prompt = load_narrative_prompt()
    payload = json.loads(old_run["request_payload_json"])
    payload.pop("output_schema_version")
    payload.update(
        security_id=legacy["security_id"],
        request_schema_version="paqs-e-narrative-request-v1",
        output_format_version="paqs-e-narrative-markdown-v1",
        prompt_version=prompt.prompt_version,
        prompt_content_sha256=prompt.content_sha256,
        web_research=False,
    )
    identity = {
        key: value
        for key, value in old_run.items()
        if key
        not in {
            "analysis_run_id",
            "validator_version",
            "validation_issues",
            "output_schema_version",
            "status",
            "request_payload_json",
            "request_payload_sha256",
            "provider_response_id",
            "failure_kind",
            "failure_reason",
            "started_at",
            "completed_at",
        }
    }
    identity.update(
        request_schema_version=payload["request_schema_version"],
        output_format_version=payload["output_format_version"],
        prompt_version=prompt.prompt_version,
        prompt_content_sha256=prompt.content_sha256,
        web_research=False,
    )
    run = {
        **identity,
        "narrative_run_id": old_run["analysis_run_id"],
        "status": "SUCCEEDED",
        "request_payload_json": canonical_json(payload),
        "request_payload_sha256": hashlib.sha256(canonical_json(payload).encode()).hexdigest(),
        "provider_response_id": "synthetic-narrative",
        "failure_kind": None,
        "failure_reason": None,
        "started_at": old_run["started_at"],
        "completed_at": old_run["completed_at"],
    }
    result = {
        **identity,
        "narrative_result_id": legacy["decision_id"],
        "narrative_run_id": run["narrative_run_id"],
        "revision_no": revision,
        "supersedes_narrative_result_id": legacy["supersedes_decision_id"],
        "response_text": prose,
        "response_text_sha256": hashlib.sha256(prose.encode()).hexdigest(),
    }
    return result, run


class Workbench:
    def __init__(
        self,
        browser: Browser,
        address: str,
        *,
        configured: bool = True,
        width: int = 1440,
        height: int = 900,
        legacy_history: bool = True,
    ) -> None:
        self.context = browser.new_context(
            viewport={"width": width, "height": height}, timezone_id="Pacific/Honolulu"
        )
        self.page = self.context.new_page()
        self.address = address
        self.posts: list[dict[str, Any]] = []
        self.requests: list[tuple[str, str]] = []
        self.errors: list[str] = []
        self.pending: list[Route] = []
        self.hold: str | None = None
        self.post_status = 201
        self.post_body: Any = None
        self.post_mode = "json"
        self.run_mode = "json"
        self.configured = configured
        self.legacy_history = legacy_history
        pair, run = narrative_pair(2)
        self.narratives = {pair["narrative_result_id"]: pair}
        self.narrative_runs = {run["narrative_run_id"]: run}
        self.narrative_history_ids: list[str] = []
        self.state_price = "111.123456789012345678"
        self.add_error = False
        self.securities = [
            dict(
                id=key,
                market=market,
                symbol=symbol,
                display_symbol=f"{market}.{symbol}",
                display_name=name,
                currency=currency,
                metadata_status="USER_SUPPLIED_UNVERIFIED",
            )
            for key, market, symbol, name, currency in (
                (US, "US", "AVGO", "Broadcom · 合成验收", "USD"),
                (HK, "HK", "00700", "腾讯 · 合成验收", "HKD"),
            )
        ]
        self.decisions: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        for revision in (1, 2):
            self.add_pair(*fixture_pair(revision))
        self.add_pair(*fixture_pair(3, market="HK"))
        self.history_ids = list(self.decisions)
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.requests.append((request.method, request.url)))
        self.page.route("**/api/v1/**", self.route)

    def add_pair(self, decision: dict[str, Any], run: dict[str, Any]) -> None:
        self.decisions[decision["decision_id"]] = decision
        self.runs[run["analysis_run_id"]] = run

    def fulfill(self, route: Route, body: Any, status: int = 200) -> None:
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(body, ensure_ascii=False),
        )

    def route(self, route: Route) -> None:
        request = route.request
        parsed = urlparse(request.url)
        path = parsed.path
        if request.method == "POST" and path.endswith("/paqs-e/narrative-analyses"):
            payload = request.post_data_json
            assert isinstance(payload, dict)
            self.posts.append(payload)
        if self.hold and self.hold in request.url:
            self.pending.append(route)
            return
        self.respond(route)

    def respond(self, route: Route) -> None:
        request = route.request
        parsed = urlparse(request.url)
        path = parsed.path
        if path.endswith("/configuration"):
            package = load_strategy_package()
            return self.fulfill(
                route,
                {
                    "default_model_key": "deepseek-v4-flash",
                    "models": [
                        {
                            "model_key": item.model_key,
                            "display_name": item.display_name,
                            "credential_label": item.credential_label,
                            "credential_configured": self.configured,
                            "web_research_supported": item.web_research_supported,
                        }
                        for item in ModelRegistry().models
                    ],
                    "default_strategy_id": STRATEGY,
                    "strategies": [
                        {
                            "strategy_id": STRATEGY,
                            "display_name": "PAQS-E 主策略",
                            "content_sha256": package.content_sha256,
                        },
                        {
                            "strategy_id": "fixture-alternative",
                            "display_name": "仅网络夹具策略",
                            "content_sha256": package.content_sha256,
                        },
                    ],
                },
            )
        if path.endswith("/paqs-e/narrative-analyses"):
            if self.post_mode == "abort":
                return route.abort("connectionfailed")
            if self.post_mode == "nonjson":
                return route.fulfill(
                    status=502, content_type="text/plain", body="synthetic non-JSON failure"
                )
            if self.post_body is None:
                selected = self.narratives["20000000-0000-4000-8000-000000000002"]
                frozen = self.narrative_runs[selected["narrative_run_id"]]
                capsule = json.loads(frozen["request_payload_json"])
                captured = request.post_data_json
                assert isinstance(captured, dict)
                enabled = captured["web_research"]
                capsule["web_research"] = selected["web_research"] = frozen["web_research"] = (
                    enabled
                )
                capsule["auxiliary_context"] = (
                    (
                        capsule["auxiliary_context"]
                        or [
                            {
                                "context_id": "synthetic-browser-research",
                                "category": "web_research",
                                "content": "Synthetic frozen source context",
                                "provenance": "https://example.org/frozen",
                            }
                        ]
                    )
                    if enabled
                    else []
                )
                frozen["request_payload_json"] = canonical_json(capsule)
                frozen["request_payload_sha256"] = hashlib.sha256(
                    canonical_json(capsule).encode()
                ).hexdigest()
            body = self.post_body or {
                **self.narratives["20000000-0000-4000-8000-000000000002"],
                "status": "SUCCEEDED",
            }
            return self.fulfill(route, body, self.post_status)
        if "/paqs-e/narrative-analyses/" in path:
            if self.run_mode == "unavailable":
                return self.fulfill(route, {"detail": "synthetic evidence unavailable"}, 500)
            return self.fulfill(route, self.narrative_runs[path.rsplit("/", 1)[1]])
        if "/paqs-e/narrative-results/" in path:
            return self.fulfill(route, self.narratives[path.rsplit("/", 1)[1]])
        if path.endswith("/narrative-results"):
            security_id = path.split("/")[-2]
            strategy = parse_qs(parsed.query).get("strategy_id", [None])[0]
            items = [self.narratives[key] for key in self.narrative_history_ids]
            items = [
                item
                for item in items
                if item["security_id"] == security_id
                and (not strategy or item["strategy_id"] == strategy)
            ]
            items.sort(key=lambda item: item["created_at"], reverse=True)
            return self.fulfill(
                route,
                {
                    "items": [
                        {
                            **{key: value for key, value in item.items() if key != "response_text"},
                            "preview": item["response_text"][:160],
                        }
                        for item in items[:20]
                    ]
                },
            )
        if "/paqs-e/analyses/" in path:
            if self.run_mode == "unavailable":
                return self.fulfill(route, {"detail": "synthetic evidence unavailable"}, 500)
            return self.fulfill(route, self.runs[path.rsplit("/", 1)[1]])
        if "/paqs-e/decisions/" in path:
            return self.fulfill(route, self.decisions[path.rsplit("/", 1)[1]])
        if "/paqs-e/securities/" in path:
            key = path.split("/")[-2]
            strategy = parse_qs(parsed.query).get("strategy_id", [None])[0]
            items = [self.decisions[key] for key in self.history_ids]
            items = [
                item
                for item in items
                if item["security_id"] == key
                and (strategy is None or item["strategy_id"] == strategy)
            ]
            items.sort(key=lambda item: item["created_at"], reverse=True)
            return self.fulfill(
                route,
                {
                    "items": [
                        {
                            key: value
                            for key, value in item.items()
                            if key not in {"result", "result_payload_sha256"}
                        }
                        for item in items[:20]
                    ]
                },
            )
        if path.endswith("/watchlist"):
            return self.fulfill(route, {"items": [{"security": item} for item in self.securities]})
        if path.endswith("/watchlist/supported-securities"):
            if self.add_error:
                return self.fulfill(
                    route, {"code": "NOT_ENTITLED", "detail": "行情权限不足 · NOT_ENTITLED"}, 422
                )
            security = dict(
                self.securities[-1]
                if self.securities
                else {
                    "id": HK,
                    "market": "HK",
                    "symbol": "00700",
                    "display_symbol": "HK.00700",
                    "display_name": "合成新增",
                    "currency": "HKD",
                }
            )
            if not any(item["id"] == security["id"] for item in self.securities):
                self.securities.append(security)
            return self.fulfill(route, {"item": {"security": security}}, 201)
        if "/watchlist/" in path and request.method == "DELETE":
            self.securities = [
                item for item in self.securities if item["id"] != path.rsplit("/", 1)[1]
            ]
            return route.fulfill(status=204)
        if "/market-data/securities/" in path:
            key = path.split("/")[-2]
            market = "HK" if key == HK else "US"
            base = {
                "security_id": key,
                "provider": "synthetic-browser-fixture",
                "status": "AVAILABLE",
                "market_timezone": "Asia/Hong_Kong" if market == "HK" else "America/New_York",
                "retrieved_at": "2026-09-04T12:00:00Z",
                "reason": None,
            }
            if path.endswith("/state"):
                return self.fulfill(
                    route,
                    {
                        **base,
                        "latest_price": self.state_price,
                        "currency": "HKD" if market == "HK" else "USD",
                        "quote_status": "AVAILABLE",
                        "market_status": "AVAILABLE",
                        "market_state": "OPEN",
                        "provider_market_state": "synthetic",
                        "latest_quote_at": base["retrieved_at"],
                    },
                )
            evidence = json.loads(
                next(run for run in self.runs.values() if run["security_id"] == key)[
                    "request_payload_json"
                ]
            )["market_snapshot"]
            bars = evidence["d1_bars" if path.endswith("daily-bars") else "m30_bars"]
            return self.fulfill(
                route,
                {
                    **base,
                    "bars": bars,
                    "latest_completed_minute_bar_at": bars[-1].get("interval_end"),
                },
            )
        route.continue_()

    def open(self) -> Page:
        self.page.goto(self.address)
        self.page.wait_for_function(
            "document.querySelector('#configuration-status').textContent !== '读取服务器配置…'"
        )
        self.page.wait_for_function(
            "document.querySelector('#history-status').textContent !== '读取成功历史…'"
        )
        self.page.evaluate("""() => {
          window.chartCaptures = [];
          const create = LightweightCharts.createChart;
          window.LightweightCharts = {...LightweightCharts, createChart: (...args) => {
            const result = create(...args), add = result.addSeries.bind(result);
            const record = {series: [], lines: []}; window.chartCaptures.push(record);
            result.addSeries = (...params) => {
              const series = add(...params), set = series.setData.bind(series);
              const data = {bars: []}; record.series.push(data);
              series.setData = bars => { data.bars = bars; return set(bars); };
              const line = series.createPriceLine.bind(series);
              const remove = series.removePriceLine.bind(series);
              series.createPriceLine = options => {
                const id = line(options); record.lines.push({id, options}); return id;
              };
              series.removePriceLine = id => {
                record.lines = record.lines.filter(item => item.id !== id); remove(id);
              };
              return series;
            }; return result;
          }};
        }""")
        if self.legacy_history:
            self.page.locator("#legacy-history-section > summary").click()
            self.page.wait_for_function(
                "document.querySelector('#legacy-history-status').textContent !== '读取成功历史…'"
            )
            self.page.locator("#known-run-kind").select_option("legacy", force=True)
        return self.page

    def select(self, revision: int = 1) -> None:
        self.page.locator(f'[data-decision-id="20000000-0000-4000-8000-{revision:012d}"]').click()
        self.page.wait_for_function(
            "document.querySelector('#evidence-status').textContent.startsWith('冻结 ')"
        )

    def analyze(self) -> None:
        self.page.locator("#model-id").select_option(MODEL)
        self.page.locator("#analyze-button").click()

    def close(self) -> None:
        self.context.close()

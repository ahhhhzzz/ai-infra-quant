"""Explicit, immutable product use of the accepted PAQS-Q reference engines."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol, cast

from ai_infra_quant.application.paqs_market_snapshot_queries import PaqsMarketSnapshotQueries
from ai_infra_quant.application.paqs_q_event_artifacts import load_event_registry
from ai_infra_quant.application.paqs_q_holder import conditional_holder
from ai_infra_quant.application.paqs_q_product_input import adapt_snapshot
from ai_infra_quant.application.paqs_q_setup_artifacts import run as run_setup
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.setup_reference import SetupFact, SetupRun
from ai_infra_quant.core.strategy.paqs_q.event_context import CONTEXT_ID, EVENT_ID

PRODUCT_ID = "paqs-q-product-analysis"
PRODUCT_VERSION = "1.0.0"
EVIDENCE_GUIDANCE = {
    "HISTORICAL_PRICE_AVAILABILITY_UNKNOWN": (
        "提供逐根历史行情的真实 available_at; 当前抓取时间不能替代。"
    ),
    "HISTORICAL_CALENDAR_AVAILABILITY_UNKNOWN": "提供每条交易日历事实的历史 available_at。",
    "CLOSED_DAY_FACTS_UNAVAILABLE": (
        "提供覆盖分析区间的逐日 OPEN/CLOSED 日历事实, 包含周末与假日版本。"
    ),
    "DERIVED_BAR_SOURCE_RETRIEVAL_UNAVAILABLE": "保留 W1/M30 来源分钟线的独立检索与版本证据。",
    "INDEPENDENT_M30_OPEN_REFERENCE_MISSING": (
        "若需下一根 M30 开盘资格, 须提供当时收到的独立开盘价及 available_at; "
        "不可回填已完成 K 线 open。"
    ),
    "ADJUSTMENT_HISTORY_NOT_POINT_IN_TIME": (
        "提供当时生效的复权版本及可知时间, 才能评估严格历史 AS_OF。"
    ),
    "CURRENT_QFQ_NOT_POINT_IN_TIME": "当前前复权只适合观察性分析, 不能证明历史时点可见的价格。",
    "M30_COVERAGE_INCOMPLETE": "补齐常规时段完成 M30 的缺失区间及来源记录。",
}


class AnalysisLedger(Protocol):
    def record(
        self, *, security_id: str, snapshot_hash: str, status: str, payload: dict[str, Any]
    ) -> dict[str, Any]: ...


def _json(value: object) -> Any:
    return json.loads(canonical_json(value))


def _code_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def artifact_location() -> tuple[Path, bool]:
    source_root = Path(__file__).resolve().parents[3]
    if (source_root / "src/ai_infra_quant/resources/paqs_q/setup-risk-1.0.1.json").is_file():
        return source_root, False
    wheel_root = Path(__file__).resolve().parents[2]
    if (wheel_root / "ai_infra_quant/resources/paqs_q/setup-risk-1.0.1.json").is_file():
        return wheel_root, True
    raise ValueError("PAQS_Q_SETUP_ARTIFACT_NOT_INSTALLED")


def _latest_entry(setup: SetupRun) -> list[dict[str, Any]]:
    by_setup: dict[str, list[SetupFact]] = {}
    for fact in setup.facts:
        by_setup.setdefault(fact.setup_key, []).append(fact)
    output: list[dict[str, Any]] = []
    for key, facts in sorted(by_setup.items()):
        latest = max(enumerate(facts), key=lambda pair: (pair[1].effective_at, pair[0]))[1]
        stage_a = next(
            (f for f in reversed(facts) if f.status == "ENTRY_PENDING_REVALIDATION"), None
        )
        stage_b = next(
            (
                f
                for f in reversed(facts)
                if stage_a is not None
                and f.candidate_key is not None
                and f.candidate_key == stage_a.candidate_key
                and f.effective_at >= stage_a.effective_at
                if f.status
                in {
                    "LONG_READY",
                    "OBSERVATIONAL_LONG_QUALIFIED",
                    "VALID_SETUP_BUT_POOR_ENTRY",
                    "NO_TRADE",
                }
            ),
            None,
        )
        timely_open = bool(
            stage_b
            and stage_b.entry_reference_price_at is not None
            and stage_b.entry_reference_available_at is not None
            and stage_b.entry_reference_available_at <= stage_b.entry_reference_price_at
        )
        output.append(
            {
                "setup_key": key,
                "family": latest.family,
                "variant": latest.variant,
                "latest_status": latest.status,
                "entry_advisory": latest.entry_advisory,
                "latest_fact_key": latest.fact_key,
                "effective_at": latest.effective_at,
                "anchor_price": latest.anchor_price,
                "invalidation_buffer_atr": latest.invalidation_buffer_atr,
                "risk_reference_price": latest.risk_reference_price,
                "reference_price": latest.reference_price,
                "target1": latest.target1.model_dump() if latest.target1 else None,
                "target2": latest.target2.model_dump() if latest.target2 else None,
                "rr_t1": latest.rr_t1,
                "rr_t2": latest.rr_t2,
                "reasons": latest.reasons,
                "confirmation_stage_a": stage_a.fact_key if stage_a else None,
                "confirmation_candidate_key": stage_a.candidate_key if stage_a else None,
                "confirmation_indicative": (
                    {
                        "effective_at": stage_a.effective_at,
                        "reference_price": stage_a.reference_price,
                        "invalidation_price": stage_a.risk_reference_price,
                        "target1": stage_a.target1.model_dump() if stage_a.target1 else None,
                        "target2": stage_a.target2.model_dump() if stage_a.target2 else None,
                        "rr_t1": stage_a.rr_t1,
                        "rr_t2": stage_a.rr_t2,
                        "reasons": stage_a.reasons,
                    }
                    if stage_a
                    else None
                ),
                "next_open_stage_b": stage_b.fact_key if stage_b else None,
                "next_open_candidate_key": stage_b.candidate_key if stage_b else None,
                "next_open_qualification": (
                    {
                        "effective_at": stage_b.effective_at,
                        "available_at": stage_b.entry_reference_available_at,
                        "source": stage_b.entry_reference_source,
                        "source_ref": stage_b.entry_reference_source_ref,
                        "timely_open_reference": timely_open,
                        "status": stage_b.status,
                        "reference_price": stage_b.reference_price,
                        "invalidation_price": stage_b.risk_reference_price,
                        "target1": stage_b.target1.model_dump() if stage_b.target1 else None,
                        "target2": stage_b.target2.model_dump() if stage_b.target2 else None,
                        "rr_t1": stage_b.rr_t1,
                        "rr_t2": stage_b.rr_t2,
                        "reasons": stage_b.reasons,
                    }
                    if stage_b
                    else None
                ),
                "independent_open_observed": timely_open,
            }
        )
    return cast(list[dict[str, Any]], _json(output))


class PaqsQProductAnalysisService:
    def __init__(
        self,
        captures: PaqsMarketSnapshotQueries,
        ledger: AnalysisLedger,
        *,
        artifact_root: Path | None = None,
        wheel: bool | None = None,
    ) -> None:
        self.captures = captures
        self.ledger = ledger
        if artifact_root is None:
            self.artifact_root, self.wheel = artifact_location()
        else:
            self.artifact_root, self.wheel = artifact_root, bool(wheel)

    def analyze(self, security_id: str) -> dict[str, Any]:
        snapshot, source = self.captures.current_capture(security_id)
        if snapshot.security.security_id != security_id:
            raise ValueError("PRODUCT_CAPTURE_SECURITY_MISMATCH")
        adapted = adapt_snapshot(snapshot, source)
        bundle = adapted.multi_input
        registry = load_event_registry(self.artifact_root, wheel=self.wheel)
        context: dict[str, Any] = {}
        event: dict[str, Any] = {}
        inputs: dict[str, Any] = {}
        for name, data in (("W1", bundle.w1), ("D1", bundle.d1), ("M30", bundle.m30)):
            if data is None:
                context[name] = {
                    "status": "INSUFFICIENT",
                    "reason_codes": [f"{name}_INPUT_MISSING"],
                }
                event[name] = {"status": "INSUFFICIENT", "reason_codes": [f"{name}_INPUT_MISSING"]}
                inputs[name] = None
                continue
            assert isinstance(data, QInput)
            inputs[name] = {"input_hash": data.input_hash, "payload": data.payload()}
            structure_result = registry.structure(data, CONTEXT_ID, "1.0.1")
            event_result = registry.event(data, structure_result, EVENT_ID, "1.0.1")
            context[name] = structure_result.document()
            event[name] = event_result.document()
        setup = run_setup(bundle, self.artifact_root, wheel=self.wheel)
        holder = conditional_holder(setup, bundle.m30)
        diagnostics = list(dict.fromkeys((*adapted.diagnostics, *setup.reasons)))
        guidance = [
            {
                "code": code,
                "action": EVIDENCE_GUIDANCE.get(
                    code, "查看冻结 Context/Event/Setup 原因与来源记录。"
                ),
            }
            for code in diagnostics
        ]
        payload = _json(
            {
                "product_id": PRODUCT_ID,
                "product_version": PRODUCT_VERSION,
                "product_code_hash": _code_hash(Path(__file__)),
                "adapter_code_hash": _code_hash(
                    Path(__file__).with_name("paqs_q_product_input.py")
                ),
                "market_snapshot": snapshot,
                "snapshot_hash": snapshot.snapshot_hash,
                "snapshot_as_of_timestamp": snapshot.as_of_timestamp,
                "capture_source": {
                    "input_provider": source.provider,
                    "calendar_provider": source.calendar.provider,
                    "calendar_retrieved_at": source.calendar.retrieved_at,
                    "adjustment_basis": source.adjustment.basis,
                    "adjustment_as_of": source.adjustment.adjustment_as_of,
                    "historical_replay_safe": source.adjustment.historical_replay_safe,
                    "source_coverage": source.source_coverage,
                },
                "q_inputs": inputs,
                "context": context,
                "event": event,
                "setup": setup.model_dump(),
                "entry": _latest_entry(setup),
                "holder": holder,
                "diagnostics": diagnostics,
                "evidence_guidance": guidance,
                "qualification_mode": "OBSERVATIONAL",
                "strict_historical_as_of": False,
                "entry_reference_count": len(bundle.entry_references),
            }
        )
        return self.ledger.record(
            security_id=security_id,
            snapshot_hash=snapshot.snapshot_hash,
            status=setup.status,
            payload=payload,
        )

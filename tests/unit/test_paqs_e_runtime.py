from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from enum import StrEnum
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import TypeAdapter, ValidationError

import ai_infra_quant.application.paqs_e_runtime as runtime_module
from ai_infra_quant.application.paqs_e_runtime import (
    PaqsEReasoningRuntime,
    RuntimePackageError,
    build_reasoning_request,
    load_prompt_package,
    load_strategy_package,
    validate_reasoning_result,
)
from ai_infra_quant.core.domain.enums import (
    DataAvailabilityStatus,
    InstrumentType,
    RecordSource,
    SnapshotQualityStatus,
    TradabilityStatus,
    VerificationStatus,
)
from ai_infra_quant.core.domain.market_data import (
    CanonicalMarketState,
    DailyBar,
    MarketStatusSnapshot,
    ProviderResult,
    QuoteSnapshot,
)
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    PAQS_E_ENTRY_REFERENCE_POLICY_V1,
    PAQS_E_OUTPUT_SCHEMA_VERSION,
    PAQS_E_QUOTE_FRESHNESS_POLICY_V1,
    PAQS_E_REQUEST_SCHEMA_VERSION,
    PAQS_E_VALIDATOR_VERSION,
    AnalysisMode,
    AuxiliaryContextItem,
    ChaseRisk,
    ContextAssessment,
    ContextState,
    CurrentLocation,
    CurrentPriceOutput,
    EntryAdvisory,
    EntryAssessment,
    EventType,
    ExecutableEntryOutput,
    FollowthroughStatus,
    FreshnessStatus,
    HolderAdvisory,
    HolderAdvisoryBasis,
    HolderAssessment,
    InputQuality,
    InvalidationAssessment,
    InvalidationStrength,
    KeyLevel,
    LocationQuality,
    MarketBias,
    PaqsEReasoningRequestV1,
    PaqsEReasoningResultV1,
    PaqsERuntimeConfigV1,
    PaqsERuntimeGuardrails,
    PaqsEValidationFailure,
    PriceActionAssessment,
    PriceReferences,
    PriceSessionType,
    ResultIdentity,
    RiskRewardAssessment,
    RRStatus,
    SetupAssessment,
    SetupDirection,
    SetupExpiryReason,
    SetupFamily,
    SetupStage,
    SupportAssessment,
    SupportStatus,
    TargetsAssessment,
    TimeframeContext,
    TriggerStatus,
    UncertaintyAssessment,
    UncertaintyLevel,
    ValidatedPaqsEResult,
)
from ai_infra_quant.core.domain.paqs_input import (
    AdjustmentBasis,
    AdjustmentMetadata,
    CalendarMetadata,
    DerivedBar,
    DerivedCoverage,
    DerivedTimeframe,
    PaqsInputBundle,
    SourceCoverage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import (
    PaqsMarketSnapshot,
    build_paqs_market_snapshot,
    canonical_json,
)
from ai_infra_quant.core.domain.security import Security
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    ReasoningFailureKind,
    ReasoningProviderFailure,
    ReasoningProviderSuccess,
)
from ai_infra_quant.integrations.openai_reasoning.adapter import (
    OpenAIPaqsEReasoningAdapter,
)
from ai_infra_quant.integrations.openai_reasoning.schema import (
    PaqsEReasoningResultSchemaV1,
)

NOW = datetime(2026, 9, 4, 12, tzinfo=UTC)
SECURITY_ID = "00000000-0000-4000-8000-000000000007"


def _snapshot(
    *, data_quality: SnapshotQualityStatus = SnapshotQualityStatus.COMPLETE
) -> PaqsMarketSnapshot:
    daily = DailyBar(
        security="US.AVGO",
        session_date=date(2026, 9, 3),
        provider_time=NOW - timedelta(days=1),
        open=Decimal("99"),
        high=Decimal("102"),
        low=Decimal("98"),
        close=Decimal("101"),
        volume=Decimal("1000"),
        is_completed=True,
        retrieved_at=NOW,
    )
    weekly = DerivedBar(
        security="US.AVGO",
        timeframe=DerivedTimeframe.W1,
        interval_start=NOW - timedelta(days=7),
        interval_end=NOW - timedelta(hours=1),
        open=Decimal("95"),
        high=Decimal("103"),
        low=Decimal("94"),
        close=Decimal("101"),
        volume=Decimal("5000"),
        market_timezone="America/New_York",
        session_type=None,
        source_bar_count=4,
        expected_source_bar_count=4,
        coverage=DerivedCoverage.COMPLETE,
        is_completed=True,
    )
    m30 = DerivedBar(
        security="US.AVGO",
        timeframe=DerivedTimeframe.M30,
        interval_start=NOW - timedelta(hours=1),
        interval_end=NOW - timedelta(minutes=30),
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=Decimal("500"),
        market_timezone="America/New_York",
        session_type="REGULAR",
        source_bar_count=30,
        expected_source_bar_count=30,
        coverage=DerivedCoverage.COMPLETE,
        is_completed=True,
    )
    bundle = PaqsInputBundle(
        security_id=SECURITY_ID,
        market="US",
        symbol="AVGO",
        market_timezone="America/New_York",
        provider="fixture",
        as_of_timestamp=NOW,
        completed_w1_bars=(weekly,),
        completed_d1_bars=(daily,),
        completed_30m_bars=(m30,),
        calendar=CalendarMetadata(
            status=DataAvailabilityStatus.AVAILABLE,
            provider="fixture",
            retrieved_at=NOW,
            trading_days=(),
        ),
        adjustment=AdjustmentMetadata(
            basis=AdjustmentBasis.PROVIDER_QFQ_CURRENT,
            adjustment_as_of=NOW,
            historical_replay_safe=False,
        ),
        data_quality=data_quality,
        warnings=(),
        source_coverage=SourceCoverage(
            d1_source_count=1,
            w1_completed_count=1,
            w1_partial_count=0,
            minute_source_count=30,
            m30_completed_count=1,
            m30_partial_count=0,
        ),
    )
    security = Security(
        id=SECURITY_ID,
        market="US",
        symbol="AVGO",
        currency="USD",
        display_name="Broadcom",
        instrument_type=InstrumentType.EQUITY,
        enabled=True,
        record_source=RecordSource.SYSTEM_SEED,
        verification_status=VerificationStatus.SYSTEM_SEED_UNVERIFIED,
        tradability_status=TradabilityStatus.UNVERIFIED,
        metadata_status=DataAvailabilityStatus.UNAVAILABLE,
        created_at=NOW,
        updated_at=NOW,
    )
    quote = ProviderResult(
        status=DataAvailabilityStatus.AVAILABLE,
        provider="fixture",
        retrieved_at=NOW,
        provider_delay_seconds=15,
        data=QuoteSnapshot(
            security="US.AVGO",
            price=Decimal("123.45"),
            currency="USD",
            latest_quote_at=NOW,
            retrieved_at=NOW,
            is_equity=True,
        ),
    )
    state = ProviderResult(
        status=DataAvailabilityStatus.AVAILABLE,
        provider="fixture",
        retrieved_at=NOW,
        data=MarketStatusSnapshot(
            security="US.AVGO",
            state=CanonicalMarketState.OPEN,
            provider_state="MORNING",
            retrieved_at=NOW,
        ),
    )
    return build_paqs_market_snapshot(
        bundle=bundle,
        security=security,
        quote_result=quote,
        market_state_result=state,
        d1_source_status=DataAvailabilityStatus.AVAILABLE,
        minute_source_status=DataAvailabilityStatus.AVAILABLE,
        created_at=NOW,
    )


def _identity(request: PaqsEReasoningRequestV1) -> ResultIdentity:
    return ResultIdentity(
        request_schema_version=request.request_schema_version,
        output_schema_version=request.output_schema_version,
        snapshot_hash=request.snapshot_hash,
        symbol=request.symbol,
        market=request.market,
        instrument_type=request.instrument_type,
        snapshot_as_of_timestamp=request.snapshot_as_of_timestamp,
        analysis_mode=request.analysis_mode,
        runtime_config_version=request.runtime_config_version,
        prompt_version=request.prompt_version,
        prompt_content_sha256=request.prompt_content_sha256,
        model_provider=request.model_provider,
        model_id=request.model_id,
        primary_strategy_id=request.primary_strategy_id,
        primary_strategy_content_sha256=request.primary_strategy_content_sha256,
    )


def _result(request: PaqsEReasoningRequestV1) -> PaqsEReasoningResultV1:
    context = TimeframeContext(states=(ContextState.UNCERTAIN,), evidence="fixture")
    return PaqsEReasoningResultV1(
        identity=_identity(request),
        support=SupportAssessment(
            support_status=SupportStatus.SUPPORTED,
            input_quality=InputQuality.COMPLETE,
            data_quality_reasons=(),
        ),
        one_line_thesis="No setup is confirmed.",
        context=ContextAssessment(
            htf=context,
            stf=context,
            ttf=context,
            regime_summary="Mixed structure.",
            trend_quality="Uncertain.",
            market_bias=MarketBias.UNCERTAIN,
            avoid_long_flag=False,
        ),
        key_levels=(
            KeyLevel(
                price_or_zone="120-124",
                role="decision zone",
                timeframe="D1",
                rationale="Visible completed-bar structure.",
                state_change="Acceptance above changes context.",
            ),
        ),
        current_location=CurrentLocation(
            description="At the decision zone.",
            quality=LocationQuality.MARGINAL,
        ),
        price_action=PriceActionAssessment(
            current_event=EventType.NONE,
            transition_states=(ContextState.UNCERTAIN,),
            trigger_status=TriggerStatus.NOT_CONFIRMED,
            followthrough_status=FollowthroughStatus.NOT_APPLICABLE,
            impulse_correction_read="No reliable trigger.",
            channel_or_exhaustion_context=None,
            structural_confirmation_uses_reference_only_quote=False,
        ),
        setup=SetupAssessment(
            family=SetupFamily.NONE,
            direction=SetupDirection.NEUTRAL,
            stage=SetupStage.NONE,
            expiry_reason=None,
            why_it_qualifies="No qualifying setup.",
            missing_confirmation=("completed trigger bar",),
            alternative_interpretation="A range may be forming.",
        ),
        price_references=PriceReferences(
            current_price_reference=CurrentPriceOutput(
                price=request.market_snapshot.current_price_reference.price,
                timestamp=request.market_snapshot.current_price_reference.latest_quote_at,
                session_type=PriceSessionType.REGULAR,
                freshness_status=FreshnessStatus.FRESH,
            ),
            executable_entry_reference=ExecutableEntryOutput(
                price=None,
                timestamp=None,
                session_type=PriceSessionType.UNKNOWN,
                freshness_status=FreshnessStatus.UNKNOWN,
                policy_basis="No eligible entry reference.",
                eligible=False,
            ),
        ),
        entry=EntryAssessment(
            advisory=EntryAdvisory.NO_SETUP,
            reference_or_zone=None,
            chase_risk=ChaseRisk.MEDIUM,
            wait_condition="Wait for completed-bar confirmation.",
        ),
        invalidation=InvalidationAssessment(
            level_or_zone=None,
            calculation_reference=None,
            condition="Unavailable without setup.",
            timeframe="D1",
            reason="No thesis to invalidate.",
            strength=InvalidationStrength.SOFT,
        ),
        targets=TargetsAssessment(
            t1_level_or_zone=None,
            t1_calculation_reference=None,
            t1_reason="Unavailable without setup.",
            t1_is_nearest_structural_obstacle=False,
            t2_level_or_zone=None,
            t2_calculation_reference=None,
            t2_reason=None,
        ),
        risk_reward=RiskRewardAssessment(
            rr_status=RRStatus.NOT_COMPUTABLE,
            executable_entry_reference=None,
            risk_per_share=None,
            rr_t1=None,
            rr_t2=None,
            rr_quality="Not computable.",
        ),
        holder=HolderAssessment(
            advisory_basis=HolderAdvisoryBasis.CURRENT_ANALYSIS_THESIS,
            prior_decision_id=None,
            advisory=HolderAdvisory.NOT_APPLICABLE,
        ),
        uncertainty=UncertaintyAssessment(
            level=UncertaintyLevel.HIGH,
            conflicting_evidence=("Mixed timeframes",),
            data_limitations=(),
        ),
        next_evidence_needed=("Completed trigger bar",),
        reason_codes=("NO_CONFIRMED_SETUP",),
        explanation="Wait for stronger evidence.",
    )


def _ready_long(result: PaqsEReasoningResultV1) -> PaqsEReasoningResultV1:
    return replace(
        result,
        setup=replace(
            result.setup,
            family=SetupFamily.A_TREND_PULLBACK_CONTINUATION,
            direction=SetupDirection.LONG,
            stage=SetupStage.CONFIRMED,
        ),
        price_references=replace(
            result.price_references,
            executable_entry_reference=ExecutableEntryOutput(
                price=Decimal("123.45"),
                timestamp=NOW,
                session_type=PriceSessionType.REGULAR,
                freshness_status=FreshnessStatus.FRESH,
                policy_basis="Regular-session executable reference.",
                eligible=True,
            ),
        ),
        price_action=replace(
            result.price_action,
            trigger_status=TriggerStatus.CONFIRMED,
            followthrough_status=FollowthroughStatus.CONFIRMED,
        ),
        entry=replace(result.entry, advisory=EntryAdvisory.LONG_READY),
        invalidation=replace(
            result.invalidation,
            level_or_zone="below 120.45 support",
            calculation_reference=Decimal("120.45"),
            condition="D1 acceptance below support.",
            reason="Breaks the setup geometry.",
            strength=InvalidationStrength.HARD,
        ),
        targets=replace(
            result.targets,
            t1_level_or_zone="129.45 resistance",
            t1_calculation_reference=Decimal("129.45"),
            t1_reason="Nearest completed-bar resistance.",
            t1_is_nearest_structural_obstacle=True,
        ),
        risk_reward=RiskRewardAssessment(
            rr_status=RRStatus.FINAL,
            executable_entry_reference=Decimal("123.45"),
            risk_per_share=Decimal("3"),
            rr_t1=Decimal("2"),
            rr_t2=None,
            rr_quality="Structurally acceptable.",
        ),
    )


def test_strategy_prompt_and_request_are_hash_bound_and_snapshot_complete() -> None:
    strategy = load_strategy_package()
    prompt = load_prompt_package()
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-test-explicit",
        strategy=strategy,
        prompt=prompt,
    )
    assert strategy.strategy_id == "paqs-e-master"
    assert strategy.source_path == "docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md"
    assert strategy.content_sha256 == hashlib.sha256(strategy.content.encode()).hexdigest()
    assert (
        strategy.content_sha256
        == "73bed86ffef402d3d1e5eff855aaa2cc4bebf1ca1aafa33500c8839f63c16f82"
    )
    assert prompt.content_sha256 == hashlib.sha256(prompt.content.encode()).hexdigest()
    assert request.request_schema_version == PAQS_E_REQUEST_SCHEMA_VERSION
    assert request.output_schema_version == PAQS_E_OUTPUT_SCHEMA_VERSION
    payload = canonical_json(request)
    for factual_field in (
        "w1_bars",
        "d1_bars",
        "m30_bars",
        "current_price_reference",
        "market_state_reference",
        "calendar_metadata",
        "adjustment_metadata",
        "timeframe_evidence_status",
        "provider_delay_seconds",
    ):
        assert f'"{factual_field}"' in payload
    assert "pivots" not in payload
    assert "zones" not in payload


def test_hashed_runtime_resources_have_explicit_lf_checkout_policy() -> None:
    attributes = set(Path(".gitattributes").read_text(encoding="utf-8").splitlines())
    assert {
        "docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md text eol=lf",
        "src/ai_infra_quant/resources/paqs_e/runtime_prompt_v1.md text eol=lf",
    }.issubset(attributes)


def test_runtime_config_and_request_identity_are_immutable_and_reject_lookahead() -> None:
    snapshot = _snapshot()
    item = AuxiliaryContextItem(
        context_id="news-1",
        category="news",
        source_label="explicit fixture",
        source_timestamp=NOW - timedelta(minutes=1),
        provenance="user supplied",
        as_of_compatible=True,
        content="Known before As-Of.",
    )
    request = build_reasoning_request(
        snapshot=snapshot,
        model_id="gpt-test-explicit",
        auxiliary_context=(item,),
    )
    assert request.auxiliary_context == (item,)
    with pytest.raises(ValueError, match="future"):
        replace(
            request,
            auxiliary_context=(replace(item, source_timestamp=NOW + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="As-Of-incompatible"):
        replace(request, auxiliary_context=(replace(item, as_of_compatible=False),))
    with pytest.raises(ValueError, match="snapshot"):
        replace(request, snapshot_hash="0" * 64)
    with pytest.raises(ValueError, match="request"):
        replace(request, symbol="NVDA")
    with pytest.raises(ValueError, match="request"):
        replace(request, market="HK")
    with pytest.raises(ValueError, match="As-Of"):
        replace(request, snapshot_as_of_timestamp=NOW - timedelta(seconds=1))
    with pytest.raises(ValueError, match="timeframe"):
        PaqsERuntimeConfigV1(ttf="H1")
    with pytest.raises(ValueError, match="current analysis"):
        replace(request, analysis_mode=AnalysisMode.HISTORICAL_ASOF_REPLAY)


def test_auxiliary_context_is_ordered_and_auditable() -> None:
    first = AuxiliaryContextItem(
        context_id="context-1",
        category="user_context",
        source_label="first",
        source_timestamp=None,
        provenance="explicit",
        as_of_compatible=True,
        content="first content",
    )
    second = replace(first, context_id="context-2", source_label="second", content="second content")
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-test-explicit",
        auxiliary_context=(first, second),
    )
    serialized = canonical_json(request)
    assert request.auxiliary_context == (first, second)
    assert serialized.index("context-1") < serialized.index("context-2")
    assert '"as_of_compatible":true' in serialized
    with pytest.raises(ValueError, match="unique"):
        replace(request, auxiliary_context=(first, first))


def test_as_of_incompatible_context_is_rejected_before_provider_input() -> None:
    incompatible = AuxiliaryContextItem(
        context_id="future-research",
        category="analyst_research",
        source_label="explicit fixture",
        source_timestamp=None,
        provenance="user supplied",
        as_of_compatible=False,
        content="This must never reach the provider.",
    )
    with pytest.raises(ValueError, match="As-Of-incompatible"):
        build_reasoning_request(
            snapshot=_snapshot(),
            model_id="gpt-test-explicit",
            auxiliary_context=(incompatible,),
        )


def test_runtime_config_requires_exact_v1_policy_identities() -> None:
    config = PaqsERuntimeConfigV1(
        entry_reference_policy=PAQS_E_ENTRY_REFERENCE_POLICY_V1,
        quote_freshness_policy=PAQS_E_QUOTE_FRESHNESS_POLICY_V1,
    )
    assert config.entry_reference_policy == "SNAPSHOT_QUOTE_REGULAR_OPEN_REQUIRED"
    assert config.quote_freshness_policy == "UPSTREAM_AVAILABLE_REQUIRED"
    with pytest.raises(ValueError, match="entry reference policy"):
        PaqsERuntimeConfigV1(entry_reference_policy="ARBITRARY_NONEMPTY_POLICY")
    with pytest.raises(ValueError, match="quote freshness policy"):
        PaqsERuntimeConfigV1(quote_freshness_policy="ARBITRARY_NONEMPTY_POLICY")

    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-test-explicit",
        runtime_config=config,
    )
    assert isinstance(
        validate_reasoning_result(request=request, result=_ready_long(_result(request))),
        ValidatedPaqsEResult,
    )


def test_strategy_loader_rejects_unregistered_and_path_traversal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(RuntimePackageError, match="not registered"):
        load_strategy_package("unknown")
    repository = tmp_path / "repository"
    registry_dir = repository / "src/ai_infra_quant/resources/paqs_e"
    registry_dir.mkdir(parents=True)
    (tmp_path / "outside.md").write_text("outside", encoding="utf-8")
    (registry_dir / "strategy_registry.json").write_text(
        json.dumps(
            {
                "default_strategy_id": "paqs-e-master",
                "strategies": [
                    {
                        "strategy_id": "paqs-e-master",
                        "display_name": "fixture",
                        "source_path": "../outside.md",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_module, "_REPOSITORY_ROOT", repository)
    with pytest.raises(RuntimePackageError, match="escapes"):
        load_strategy_package()


def test_strategy_hash_is_byte_exact_stable_and_changes_with_content(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repository = tmp_path / "repository"
    registry_dir = repository / "src/ai_infra_quant/resources/paqs_e"
    strategy_path = repository / "docs/research/strategy.md"
    registry_dir.mkdir(parents=True)
    strategy_path.parent.mkdir(parents=True)
    registry = {
        "default_strategy_id": "paqs-e-master",
        "strategies": [
            {
                "strategy_id": "paqs-e-master",
                "display_name": "fixture",
                "source_path": "docs/research/strategy.md",
            }
        ],
    }
    (registry_dir / "strategy_registry.json").write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(runtime_module, "_REPOSITORY_ROOT", repository)
    strategy_path.write_bytes(b"exact\r\nbytes\n")
    first = load_strategy_package()
    second = load_strategy_package()
    assert first.content_sha256 == second.content_sha256
    assert first.content_sha256 == hashlib.sha256(b"exact\r\nbytes\n").hexdigest()
    strategy_path.write_bytes(b"changed\n")
    assert load_strategy_package().content_sha256 != first.content_sha256
    strategy_path.unlink()
    with pytest.raises(RuntimePackageError, match="unavailable"):
        load_strategy_package()
    absolute_registry = {
        "default_strategy_id": "paqs-e-master",
        "strategies": [
            {
                "strategy_id": "paqs-e-master",
                "display_name": "fixture",
                "source_path": str((tmp_path / "absolute.md").resolve()),
            }
        ],
    }
    (registry_dir / "strategy_registry.json").write_text(
        json.dumps(absolute_registry), encoding="utf-8"
    )
    with pytest.raises(RuntimePackageError, match="repository-relative"):
        load_strategy_package()


ENUMS: tuple[type[StrEnum], ...] = (
    SupportStatus,
    InputQuality,
    ContextState,
    MarketBias,
    LocationQuality,
    EventType,
    TriggerStatus,
    FollowthroughStatus,
    SetupFamily,
    SetupDirection,
    SetupStage,
    SetupExpiryReason,
    EntryAdvisory,
    HolderAdvisoryBasis,
    HolderAdvisory,
    RRStatus,
    ChaseRisk,
    UncertaintyLevel,
    InvalidationStrength,
    PriceSessionType,
    FreshnessStatus,
)


@pytest.mark.parametrize("enum_type", ENUMS)
def test_every_exact_machine_enum_round_trips(enum_type: type[StrEnum]) -> None:
    adapter = TypeAdapter(enum_type)
    for member in enum_type:
        assert adapter.validate_json(json.dumps(member.value), strict=True) is member
    with pytest.raises(ValidationError):
        adapter.validate_json('"not-a-canonical-alias"', strict=True)


def test_strict_output_schema_requires_all_fields_forbids_extra_and_numeric_floats() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    result = _result(request)
    parsed = PaqsEReasoningResultSchemaV1.model_validate_json(canonical_json(result))
    assert parsed.to_domain() == result
    payload = json.loads(canonical_json(result))
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        PaqsEReasoningResultSchemaV1.model_validate_json(json.dumps(payload))
    del payload["unexpected"]
    del payload["explanation"]
    with pytest.raises(ValidationError):
        PaqsEReasoningResultSchemaV1.model_validate_json(json.dumps(payload))
    payload = json.loads(canonical_json(_ready_long(result)))
    payload["risk_reward"]["risk_per_share"] = 2.0
    with pytest.raises(ValidationError):
        PaqsEReasoningResultSchemaV1.model_validate_json(json.dumps(payload))
    schema = PaqsEReasoningResultSchemaV1.model_json_schema()
    assert schema["additionalProperties"] is False
    object_schemas = [schema, *schema.get("$defs", {}).values()]
    for object_schema in object_schemas:
        if object_schema.get("type") == "object":
            assert object_schema["additionalProperties"] is False
            assert set(object_schema["required"]) == set(object_schema["properties"])


def test_validator_accepts_decimal_ready_state_without_mutating_judgment() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    result = _ready_long(_result(request))
    validated = validate_reasoning_result(request=request, result=result)
    assert validated == ValidatedPaqsEResult(
        validator_version=PAQS_E_VALIDATOR_VERSION,
        provider_response_id=None,
        result=result,
    )
    assert isinstance(validated, ValidatedPaqsEResult)
    assert validated.result.entry.advisory is EntryAdvisory.LONG_READY
    with localcontext() as context:
        context.prec = 3
        assert isinstance(
            validate_reasoning_result(request=request, result=result),
            ValidatedPaqsEResult,
        )


def test_key_level_minimum_depends_on_support_quality_and_actionability() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    complete_zero = replace(_result(request), key_levels=())
    complete_failure = validate_reasoning_result(request=request, result=complete_zero)
    assert isinstance(complete_failure, PaqsEValidationFailure)
    assert "KEY_LEVELS_REQUIRED" in {issue.code for issue in complete_failure.issues}

    ready_zero = replace(_ready_long(_result(request)), key_levels=())
    ready_failure = validate_reasoning_result(request=request, result=ready_zero)
    assert isinstance(ready_failure, PaqsEValidationFailure)
    assert "KEY_LEVELS_REQUIRED" in {issue.code for issue in ready_failure.issues}

    assert isinstance(
        validate_reasoning_result(request=request, result=_result(request)),
        ValidatedPaqsEResult,
    )

    degraded_request = build_reasoning_request(
        snapshot=_snapshot(data_quality=SnapshotQualityStatus.INVALID),
        model_id="gpt-test-explicit",
    )
    degraded_base = _result(degraded_request)
    degraded = replace(
        degraded_base,
        support=SupportAssessment(
            support_status=SupportStatus.SUPPORTED,
            input_quality=InputQuality.INVALID,
            data_quality_reasons=("snapshot invalid",),
        ),
        key_levels=(),
        entry=replace(degraded_base.entry, advisory=EntryAdvisory.DATA_UNAVAILABLE),
    )
    assert isinstance(
        validate_reasoning_result(request=degraded_request, result=degraded),
        ValidatedPaqsEResult,
    )

    degraded_ready_zero = _ready_long(degraded)
    degraded_ready_failure = validate_reasoning_result(
        request=degraded_request,
        result=degraded_ready_zero,
    )
    assert isinstance(degraded_ready_failure, PaqsEValidationFailure)
    assert "KEY_LEVELS_REQUIRED" in {issue.code for issue in degraded_ready_failure.issues}


def test_validator_reports_out_of_range_ratio_instead_of_raising() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    base = _ready_long(_result(request))
    result = replace(
        base,
        invalidation=replace(
            base.invalidation,
            calculation_reference=Decimal("123.449999999999999999"),
        ),
        targets=replace(
            base.targets,
            t1_calculation_reference=Decimal("9999999999999999999"),
        ),
        risk_reward=replace(
            base.risk_reward,
            risk_per_share=Decimal("0.000000000000000001"),
            rr_t1=Decimal("9999999999999999999"),
        ),
    )
    failure = validate_reasoning_result(request=request, result=result)
    assert isinstance(failure, PaqsEValidationFailure)
    assert "RR_OUT_OF_RANGE" in {issue.code for issue in failure.issues}


def test_expiry_matrix_and_watch_short_advisory_are_enforced_separately() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    base = _result(request)
    missing_expiry = replace(base, setup=replace(base.setup, stage=SetupStage.EXPIRED))
    failure = validate_reasoning_result(request=request, result=missing_expiry)
    assert isinstance(failure, PaqsEValidationFailure)
    assert "EXPIRY_REASON_REQUIRED" in {issue.code for issue in failure.issues}
    stray_expiry = replace(
        base,
        setup=replace(
            base.setup,
            expiry_reason=SetupExpiryReason.RUNTIME_CONFIG_EXPIRY,
        ),
    )
    failure = validate_reasoning_result(request=request, result=stray_expiry)
    assert isinstance(failure, PaqsEValidationFailure)
    assert "EXPIRY_REASON_FORBIDDEN" in {issue.code for issue in failure.issues}
    watch_short = replace(
        base,
        setup=replace(
            base.setup,
            family=SetupFamily.C_RIGHT_SIDE_STRUCTURAL_BREAKOUT,
            direction=SetupDirection.SHORT,
            stage=SetupStage.CANDIDATE,
        ),
        entry=replace(base.entry, advisory=EntryAdvisory.WATCH_SHORT),
    )
    assert isinstance(
        validate_reasoning_result(request=request, result=watch_short),
        ValidatedPaqsEResult,
    )


TRIGGER_MATRIX = {
    TriggerStatus.NOT_CONFIRMED: {FollowthroughStatus.NOT_APPLICABLE},
    TriggerStatus.CONFIRMED: {
        FollowthroughStatus.PENDING,
        FollowthroughStatus.WEAK,
        FollowthroughStatus.CONFIRMED,
    },
    TriggerStatus.UNAVAILABLE: {FollowthroughStatus.UNAVAILABLE},
}
TRIGGER_CASES = tuple(
    (trigger, followthrough, followthrough in TRIGGER_MATRIX[trigger])
    for trigger in TriggerStatus
    for followthrough in FollowthroughStatus
)


@pytest.mark.parametrize(("trigger", "followthrough", "is_valid"), TRIGGER_CASES)
def test_complete_trigger_followthrough_consistency_matrix(
    trigger: TriggerStatus,
    followthrough: FollowthroughStatus,
    is_valid: bool,
) -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    base = _result(request)
    result = replace(
        base,
        price_action=replace(
            base.price_action,
            trigger_status=trigger,
            followthrough_status=followthrough,
        ),
    )
    outcome = validate_reasoning_result(request=request, result=result)
    codes = (
        set()
        if isinstance(outcome, ValidatedPaqsEResult)
        else {issue.code for issue in outcome.issues}
    )
    assert ("TRIGGER_FOLLOWTHROUGH_INCONSISTENT" not in codes) is is_valid


@pytest.mark.parametrize(
    ("changed", "expected_code"),
    [
        (
            lambda value: replace(
                value,
                invalidation=replace(
                    value.invalidation,
                    calculation_reference=Decimal("123.45"),
                ),
                risk_reward=replace(value.risk_reward, risk_per_share=Decimal("0")),
            ),
            "NON_POSITIVE_RISK",
        ),
        (
            lambda value: replace(
                value,
                targets=replace(value.targets, t1_calculation_reference=Decimal("122")),
            ),
            "TARGET_WRONG_SIDE",
        ),
        (
            lambda value: replace(
                value,
                price_references=replace(
                    value.price_references,
                    executable_entry_reference=replace(
                        value.price_references.executable_entry_reference,
                        price=None,
                        timestamp=None,
                        eligible=False,
                    ),
                ),
            ),
            "FINAL_RR_INPUT_MISSING",
        ),
    ],
)
def test_validator_rejects_nonpositive_risk_wrong_target_and_missing_final_entry(
    changed: object, expected_code: str
) -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    invalid = changed(_ready_long(_result(request)))  # type: ignore[operator]
    failure = validate_reasoning_result(request=request, result=invalid)
    assert isinstance(failure, PaqsEValidationFailure)
    assert expected_code in {issue.code for issue in failure.issues}


def test_actionable_advisory_requires_structural_and_numeric_references() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    base = _result(request)
    invalid = replace(
        base,
        setup=replace(base.setup, direction=SetupDirection.LONG, stage=SetupStage.CONFIRMED),
        entry=replace(base.entry, advisory=EntryAdvisory.LONG_READY),
    )
    failure = validate_reasoning_result(request=request, result=invalid)
    assert isinstance(failure, PaqsEValidationFailure)
    assert {
        "ACTIONABLE_ENTRY_REQUIRED",
        "STRUCTURAL_INVALIDATION_REQUIRED",
        "NEAREST_STRUCTURAL_T1_REQUIRED",
        "FINAL_RR_REQUIRED",
    }.issubset({issue.code for issue in failure.issues})


def test_versioned_minimum_rr_guardrail_is_validated_without_rewriting_result() -> None:
    config = PaqsERuntimeConfigV1(
        guardrails=PaqsERuntimeGuardrails(version="rr-policy-v1", minimum_rr_t1=Decimal("2.5"))
    )
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-test-explicit",
        runtime_config=config,
    )
    result = _ready_long(_result(request))
    failure = validate_reasoning_result(request=request, result=result)
    assert isinstance(failure, PaqsEValidationFailure)
    assert "RR_GUARDRAIL_NOT_MET" in {issue.code for issue in failure.issues}
    assert result.risk_reward.rr_t1 == Decimal("2")

    non_action = replace(result, entry=replace(result.entry, advisory=EntryAdvisory.NO_TRADE))
    validated = validate_reasoning_result(request=request, result=non_action)
    assert isinstance(validated, ValidatedPaqsEResult)
    assert validated.result is non_action
    assert validated.result.entry.advisory is EntryAdvisory.NO_TRADE
    assert validated.result.risk_reward.rr_t1 == Decimal("2")


@pytest.mark.parametrize(
    ("mutator", "code"),
    [
        (
            lambda value: replace(
                value,
                identity=replace(value.identity, model_id="fallback-model"),
            ),
            "IDENTITY_MISMATCH",
        ),
        (
            lambda value: replace(
                value,
                price_action=replace(
                    value.price_action,
                    followthrough_status=FollowthroughStatus.CONFIRMED,
                ),
            ),
            "TRIGGER_FOLLOWTHROUGH_INCONSISTENT",
        ),
        (
            lambda value: replace(
                value,
                price_action=replace(
                    value.price_action,
                    structural_confirmation_uses_reference_only_quote=True,
                ),
            ),
            "REFERENCE_QUOTE_USED_FOR_STRUCTURE",
        ),
        (
            lambda value: replace(
                value,
                price_references=replace(
                    value.price_references,
                    current_price_reference=replace(
                        value.price_references.current_price_reference,
                        price=Decimal("999"),
                    ),
                ),
            ),
            "CURRENT_PRICE_FACT_MISMATCH",
        ),
    ],
)
def test_validator_rejects_identity_state_and_snapshot_fact_violations(
    mutator: object, code: str
) -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    changed = mutator(_result(request))  # type: ignore[operator]
    failure = validate_reasoning_result(request=request, result=changed)
    assert isinstance(failure, PaqsEValidationFailure)
    assert code in {issue.code for issue in failure.issues}


def test_validator_rejects_short_ready_bad_rr_target_shopping_and_hidden_prior_decision() -> None:
    request = build_reasoning_request(snapshot=_snapshot(), model_id="gpt-test-explicit")
    long_result = _ready_long(_result(request))
    bad = replace(
        long_result,
        entry=replace(long_result.entry, advisory=EntryAdvisory.SHORT_READY),
        risk_reward=replace(long_result.risk_reward, rr_t1=Decimal("9"), rr_t2=Decimal("2.5")),
        targets=replace(
            long_result.targets,
            t2_level_or_zone="105 farther target",
            t2_calculation_reference=Decimal("105"),
            t2_reason="Not actually farther.",
        ),
        holder=HolderAssessment(
            advisory_basis=HolderAdvisoryBasis.PRIOR_DECISION_ID,
            prior_decision_id="hidden-1",
            advisory=HolderAdvisory.THESIS_VALID,
        ),
    )
    failure = validate_reasoning_result(request=request, result=bad)
    assert isinstance(failure, PaqsEValidationFailure)
    assert {
        "SHORT_EXECUTION_NOT_ALLOWED",
        "READY_DIRECTION_MISMATCH",
        "RR_ARITHMETIC_MISMATCH",
        "TARGET_ORDER_INVALID",
        "PRIOR_DECISION_NOT_SUPPLIED",
    }.issubset({issue.code for issue in failure.issues})


class _Provider:
    def __init__(self, outcome: ReasoningProviderSuccess | ReasoningProviderFailure) -> None:
        self.outcome = outcome

    def reason(self, **_: object) -> ReasoningProviderSuccess | ReasoningProviderFailure:
        return self.outcome


def test_application_runtime_preserves_typed_provider_failure_and_validates_success() -> None:
    strategy = load_strategy_package()
    prompt = load_prompt_package()
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-test-explicit",
        strategy=strategy,
        prompt=prompt,
    )
    failure = ReasoningProviderFailure(
        kind=ReasoningFailureKind.PROVIDER_UNAVAILABLE,
        reason="provider unavailable",
    )
    assert (
        PaqsEReasoningRuntime(_Provider(failure)).reason(
            request=request, strategy=strategy, prompt=prompt
        )
        == failure
    )
    success = ReasoningProviderSuccess(result=_result(request), provider_response_id="resp_1")
    outcome = PaqsEReasoningRuntime(_Provider(success)).reason(
        request=request,
        strategy=strategy,
        prompt=prompt,
    )
    assert isinstance(outcome, ValidatedPaqsEResult)
    assert outcome.provider_response_id == "resp_1"


class _FakeResponses:
    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class _FakeClient:
    def __init__(self, responses: _FakeResponses) -> None:
        self.responses = responses


def test_openai_adapter_uses_strict_stateless_responses_request_without_tools() -> None:
    strategy = load_strategy_package()
    prompt = load_prompt_package()
    compatible_context = AuxiliaryContextItem(
        context_id="research-known-at-cutoff",
        category="analyst_research",
        source_label="explicit fixture",
        source_timestamp=NOW,
        provenance="user supplied",
        as_of_compatible=True,
        content="Provider-visible compatible context.",
    )
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-explicit-no-fallback",
        strategy=strategy,
        prompt=prompt,
        auxiliary_context=(compatible_context,),
    )
    parsed = PaqsEReasoningResultSchemaV1.model_validate_json(canonical_json(_result(request)))
    responses = _FakeResponses(SimpleNamespace(output_parsed=parsed, id="resp_007a"))
    outcome = OpenAIPaqsEReasoningAdapter(client=_FakeClient(responses)).reason(
        request=request,
        strategy=strategy,
        prompt=prompt,
    )
    assert isinstance(outcome, ReasoningProviderSuccess)
    call = responses.calls[0]
    assert call["model"] == "gpt-explicit-no-fallback"
    assert call["text_format"] is PaqsEReasoningResultSchemaV1
    assert call["store"] is False
    assert {"tools", "previous_response_id", "conversation", "background"}.isdisjoint(call)
    assert prompt.content in str(call["instructions"])
    provider_input = call["input"]
    assert isinstance(provider_input, list)
    assert strategy.content in provider_input[0]["content"]
    assert '"timeframe_evidence_status"' in str(call["input"])
    assert compatible_context.content in str(call["input"])


def test_openai_adapter_returns_truthful_typed_failures_without_secret_leakage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = load_strategy_package()
    prompt = load_prompt_package()
    request = build_reasoning_request(
        snapshot=_snapshot(),
        model_id="gpt-test-explicit",
        strategy=strategy,
        prompt=prompt,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    missing = OpenAIPaqsEReasoningAdapter().reason(
        request=request, strategy=strategy, prompt=prompt
    )
    assert isinstance(missing, ReasoningProviderFailure)
    assert missing.kind is ReasoningFailureKind.CONFIGURATION_ERROR
    secret = "test-only-provider-secret"
    failed_responses = _FakeResponses(error=RuntimeError(secret))
    unavailable = OpenAIPaqsEReasoningAdapter(
        api_key=secret,
        client=_FakeClient(failed_responses),
    ).reason(request=request, strategy=strategy, prompt=prompt)
    assert isinstance(unavailable, ReasoningProviderFailure)
    assert unavailable.kind is ReasoningFailureKind.PROVIDER_UNAVAILABLE
    assert secret not in unavailable.reason
    refusal_part = SimpleNamespace(type="refusal", refusal="declined")
    refusal_response = SimpleNamespace(
        output_parsed=None,
        output=[SimpleNamespace(content=[refusal_part])],
    )
    refusal = OpenAIPaqsEReasoningAdapter(
        client=_FakeClient(_FakeResponses(refusal_response))
    ).reason(request=request, strategy=strategy, prompt=prompt)
    assert isinstance(refusal, ReasoningProviderFailure)
    assert refusal.kind is ReasoningFailureKind.PROVIDER_REFUSAL
    invalid = OpenAIPaqsEReasoningAdapter(
        client=_FakeClient(_FakeResponses(SimpleNamespace(output_parsed={"not": "strict"})))
    ).reason(request=request, strategy=strategy, prompt=prompt)
    assert isinstance(invalid, ReasoningProviderFailure)
    assert invalid.kind is ReasoningFailureKind.INVALID_STRUCTURED_OUTPUT
    tampered_strategy = replace(strategy, content=f"{strategy.content}\ntampered")
    tampered = OpenAIPaqsEReasoningAdapter(
        client=_FakeClient(_FakeResponses(SimpleNamespace(output_parsed=None)))
    ).reason(request=request, strategy=tampered_strategy, prompt=prompt)
    assert isinstance(tampered, ReasoningProviderFailure)
    assert tampered.kind is ReasoningFailureKind.CONFIGURATION_ERROR


def test_strategy_body_is_not_duplicated_in_openai_adapter_source() -> None:
    strategy = load_strategy_package()
    adapter_source = Path("src/ai_infra_quant/integrations/openai_reasoning/adapter.py").read_text(
        encoding="utf-8"
    )
    assert strategy.content not in adapter_source

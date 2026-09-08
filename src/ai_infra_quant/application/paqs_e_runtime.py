from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import localcontext
from pathlib import Path
from typing import Any

from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, SnapshotQualityStatus
from ai_infra_quant.core.domain.market_data import CanonicalMarketState
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    OPENAI_PROVIDER_ID,
    PAQS_E_DEFAULT_STRATEGY_ID,
    PAQS_E_OUTPUT_SCHEMA_VERSION,
    PAQS_E_PROMPT_VERSION,
    PAQS_E_REQUEST_SCHEMA_VERSION,
    PAQS_E_VALIDATOR_VERSION,
    AnalysisMode,
    AuxiliaryContextItem,
    EntryAdvisory,
    FollowthroughStatus,
    FreshnessStatus,
    HolderAdvisoryBasis,
    InputQuality,
    PaqsEReasoningRequestV1,
    PaqsEReasoningResultV1,
    PaqsERuntimeConfigV1,
    PaqsEValidationFailure,
    PriceSessionType,
    PromptPackage,
    ResultIdentity,
    RRStatus,
    SetupDirection,
    SetupStage,
    StrategyPackage,
    SupportStatus,
    TriggerStatus,
    ValidatedPaqsEResult,
    ValidationIssue,
    decimal_ratio,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    PaqsEReasoningProvider,
    ReasoningFailureKind,
    ReasoningProviderFailure,
    ReasoningProviderOutcome,
    ReasoningProviderSuccess,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_RESOURCE_ROOT = Path("src/ai_infra_quant/resources/paqs_e")
_STRATEGY_REGISTRY = _RESOURCE_ROOT / "strategy_registry.json"
_PROMPT_RESOURCE = _RESOURCE_ROOT / "runtime_prompt_v1.md"


class RuntimePackageError(ValueError):
    pass


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_registered_markdown(relative_path: str) -> tuple[str, str]:
    candidate = Path(relative_path)
    if candidate.is_absolute() or candidate.suffix.lower() != ".md":
        raise RuntimePackageError("registered strategy path must be repository-relative Markdown")
    repository_root = _REPOSITORY_ROOT.resolve()
    resolved = (repository_root / candidate).resolve()
    if not resolved.is_relative_to(repository_root):
        raise RuntimePackageError("registered strategy path escapes the repository")
    try:
        content_bytes = resolved.read_bytes()
    except OSError as exc:
        raise RuntimePackageError("registered strategy Markdown is unavailable") from exc
    try:
        content = content_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimePackageError("registered strategy Markdown is not valid UTF-8") from exc
    return content, _sha256(content_bytes)


def load_strategy_package(strategy_id: str = PAQS_E_DEFAULT_STRATEGY_ID) -> StrategyPackage:
    registry_path = (_REPOSITORY_ROOT / _STRATEGY_REGISTRY).resolve()
    try:
        registry: object = json.loads(registry_path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimePackageError("PAQS-E strategy registry is unavailable or invalid") from exc
    if not isinstance(registry, dict) or set(registry) != {"default_strategy_id", "strategies"}:
        raise RuntimePackageError("PAQS-E strategy registry has an invalid shape")
    entries = registry["strategies"]
    if not isinstance(entries, list):
        raise RuntimePackageError("PAQS-E strategy registry entries must be a list")
    selected: dict[str, Any] | None = None
    seen: set[str] = set()
    for value in entries:
        if not isinstance(value, dict) or set(value) != {
            "strategy_id",
            "display_name",
            "source_path",
        }:
            raise RuntimePackageError("PAQS-E strategy registry entry is invalid")
        entry = value
        entry_id = entry["strategy_id"]
        if not isinstance(entry_id, str) or not entry_id or entry_id in seen:
            raise RuntimePackageError("PAQS-E strategy ids must be unique non-empty strings")
        seen.add(entry_id)
        if entry_id == strategy_id:
            selected = entry
    if registry["default_strategy_id"] != PAQS_E_DEFAULT_STRATEGY_ID:
        raise RuntimePackageError("PAQS-E default strategy id is invalid")
    if PAQS_E_DEFAULT_STRATEGY_ID not in seen:
        raise RuntimePackageError("PAQS-E default strategy is not registered")
    if selected is None:
        raise RuntimePackageError("requested PAQS-E strategy is not registered")
    display_name = selected["display_name"]
    source_path = selected["source_path"]
    if not isinstance(display_name, str) or not display_name.strip():
        raise RuntimePackageError("registered strategy display name is invalid")
    if not isinstance(source_path, str):
        raise RuntimePackageError("registered strategy source path is invalid")
    content, content_sha256 = _read_registered_markdown(source_path)
    return StrategyPackage(
        strategy_id=strategy_id,
        display_name=display_name,
        source_path=source_path,
        content_sha256=content_sha256,
        content=content,
    )


def load_prompt_package() -> PromptPackage:
    source_path = _PROMPT_RESOURCE.as_posix()
    content, content_sha256 = _read_registered_markdown(source_path)
    return PromptPackage(
        prompt_version=PAQS_E_PROMPT_VERSION,
        source_path=source_path,
        content_sha256=content_sha256,
        content=content,
    )


def build_reasoning_request(
    *,
    snapshot: PaqsMarketSnapshot,
    model_id: str,
    model_provider: str = OPENAI_PROVIDER_ID,
    runtime_config: PaqsERuntimeConfigV1 | None = None,
    strategy: StrategyPackage | None = None,
    prompt: PromptPackage | None = None,
    auxiliary_context: tuple[AuxiliaryContextItem, ...] = (),
    analysis_mode: AnalysisMode = AnalysisMode.CURRENT_ANALYSIS,
) -> PaqsEReasoningRequestV1:
    selected_config = runtime_config or PaqsERuntimeConfigV1()
    selected_strategy = strategy or load_strategy_package()
    selected_prompt = prompt or load_prompt_package()
    return PaqsEReasoningRequestV1(
        request_schema_version=PAQS_E_REQUEST_SCHEMA_VERSION,
        snapshot_hash=snapshot.snapshot_hash,
        symbol=snapshot.security.symbol,
        market=snapshot.security.market,
        instrument_type=snapshot.security.instrument_type,
        snapshot_as_of_timestamp=snapshot.as_of_timestamp,
        analysis_mode=analysis_mode,
        runtime_config_version=selected_config.runtime_config_version,
        prompt_version=selected_prompt.prompt_version,
        prompt_content_sha256=selected_prompt.content_sha256,
        output_schema_version=PAQS_E_OUTPUT_SCHEMA_VERSION,
        model_provider=model_provider,
        model_id=model_id,
        primary_strategy_id=selected_strategy.strategy_id,
        primary_strategy_content_sha256=selected_strategy.content_sha256,
        runtime_config=selected_config,
        market_snapshot=snapshot,
        auxiliary_context=auxiliary_context,
    )


def _identity_for(request: PaqsEReasoningRequestV1) -> ResultIdentity:
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


def _issue(code: str, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(code=code, field=field, message=message)


def validate_reasoning_result(
    *,
    request: PaqsEReasoningRequestV1,
    result: PaqsEReasoningResultV1,
    provider_response_id: str | None = None,
) -> ValidatedPaqsEResult | PaqsEValidationFailure:
    issues: list[ValidationIssue] = []
    if result.identity != _identity_for(request):
        issues.append(_issue("IDENTITY_MISMATCH", "identity", "result identity must match request"))

    expected_quality = {
        SnapshotQualityStatus.COMPLETE: InputQuality.COMPLETE,
        SnapshotQualityStatus.PARTIAL: InputQuality.PARTIAL,
        SnapshotQualityStatus.INVALID: InputQuality.INVALID,
    }[request.market_snapshot.data_quality]
    if result.support.input_quality is not expected_quality:
        issues.append(
            _issue(
                "INPUT_QUALITY_MISMATCH",
                "support.input_quality",
                "input quality must reflect the bound snapshot",
            )
        )
    expected_support = (
        SupportStatus.SUPPORTED
        if request.market in request.runtime_config.supported_market_scope
        and request.instrument_type in request.runtime_config.supported_instrument_scope
        else SupportStatus.UNSUPPORTED
    )
    if result.support.support_status is not expected_support:
        issues.append(
            _issue(
                "SUPPORT_STATUS_MISMATCH",
                "support.support_status",
                "support status must reflect the runtime scope",
            )
        )

    ready = result.entry.advisory in {EntryAdvisory.LONG_READY, EntryAdvisory.SHORT_READY}
    if not result.key_levels and (
        (
            result.support.support_status is SupportStatus.SUPPORTED
            and result.support.input_quality is InputQuality.COMPLETE
        )
        or ready
    ):
        issues.append(
            _issue(
                "KEY_LEVELS_REQUIRED",
                "key_levels",
                "supported complete or actionable analysis requires one to four key levels",
            )
        )

    allowed_followthrough = {
        TriggerStatus.NOT_CONFIRMED: {FollowthroughStatus.NOT_APPLICABLE},
        TriggerStatus.CONFIRMED: {
            FollowthroughStatus.PENDING,
            FollowthroughStatus.WEAK,
            FollowthroughStatus.CONFIRMED,
        },
        TriggerStatus.UNAVAILABLE: {FollowthroughStatus.UNAVAILABLE},
    }
    if (
        result.price_action.followthrough_status
        not in allowed_followthrough[result.price_action.trigger_status]
    ):
        issues.append(
            _issue(
                "TRIGGER_FOLLOWTHROUGH_INCONSISTENT",
                "price_action.followthrough_status",
                "follow-through state conflicts with trigger state",
            )
        )
    if result.setup.stage is SetupStage.EXPIRED and result.setup.expiry_reason is None:
        issues.append(
            _issue(
                "EXPIRY_REASON_REQUIRED",
                "setup.expiry_reason",
                "expired setup requires an expiry reason",
            )
        )
    if result.setup.stage is not SetupStage.EXPIRED and result.setup.expiry_reason is not None:
        issues.append(
            _issue(
                "EXPIRY_REASON_FORBIDDEN",
                "setup.expiry_reason",
                "expiry reason is only allowed for expired setup",
            )
        )
    if result.entry.advisory is EntryAdvisory.SHORT_READY and not (
        request.runtime_config.short_execution_allowed
    ):
        issues.append(
            _issue(
                "SHORT_EXECUTION_NOT_ALLOWED",
                "entry.advisory",
                "SHORT_READY is not permitted by runtime configuration",
            )
        )
    if result.entry.advisory is EntryAdvisory.WATCH_SHORT and not (
        request.runtime_config.short_advisory_allowed
    ):
        issues.append(
            _issue(
                "SHORT_ADVISORY_NOT_ALLOWED",
                "entry.advisory",
                "WATCH_SHORT is not permitted by runtime configuration",
            )
        )
    if result.price_action.structural_confirmation_uses_reference_only_quote:
        issues.append(
            _issue(
                "REFERENCE_QUOTE_USED_FOR_STRUCTURE",
                "price_action.structural_confirmation_uses_reference_only_quote",
                "reference-only quote cannot confirm completed-bar structure",
            )
        )

    snapshot_quote = request.market_snapshot.current_price_reference
    current = result.price_references.current_price_reference
    if current.price != snapshot_quote.price or current.timestamp != snapshot_quote.latest_quote_at:
        issues.append(
            _issue(
                "CURRENT_PRICE_FACT_MISMATCH",
                "price_references.current_price_reference",
                "current price reference must match the bound snapshot",
            )
        )
    expected_freshness = {
        DataAvailabilityStatus.AVAILABLE: FreshnessStatus.FRESH,
        DataAvailabilityStatus.STALE: FreshnessStatus.STALE,
        DataAvailabilityStatus.DELAYED: FreshnessStatus.DELAYED,
    }.get(snapshot_quote.status, FreshnessStatus.UNKNOWN)
    if current.freshness_status is not expected_freshness:
        issues.append(
            _issue(
                "CURRENT_PRICE_FRESHNESS_MISMATCH",
                "price_references.current_price_reference.freshness_status",
                "current-price freshness must reflect snapshot availability status",
            )
        )
    market_state = request.market_snapshot.market_state_reference
    expected_session = (
        PriceSessionType.UNKNOWN
        if market_state.canonical_state is None
        else {
            CanonicalMarketState.OPEN: PriceSessionType.REGULAR,
            CanonicalMarketState.PRE_MARKET: PriceSessionType.PRE,
            CanonicalMarketState.AFTER_HOURS: PriceSessionType.POST,
            CanonicalMarketState.CLOSED: PriceSessionType.CLOSED_REFERENCE,
        }.get(market_state.canonical_state, PriceSessionType.UNKNOWN)
    )
    if current.session_type is not expected_session:
        issues.append(
            _issue(
                "CURRENT_PRICE_SESSION_MISMATCH",
                "price_references.current_price_reference.session_type",
                "current-price session must reflect snapshot market state",
            )
        )

    holder = result.holder
    if holder.advisory_basis is HolderAdvisoryBasis.PRIOR_DECISION_ID:
        matches = tuple(
            item
            for item in request.auxiliary_context
            if item.category == "previous_paqs_e_result"
            and item.context_id == holder.prior_decision_id
        )
        if holder.prior_decision_id is None or not matches:
            issues.append(
                _issue(
                    "PRIOR_DECISION_NOT_SUPPLIED",
                    "holder.prior_decision_id",
                    "prior decision must be explicit in auxiliary context",
                )
            )
    elif holder.prior_decision_id is not None:
        issues.append(
            _issue(
                "PRIOR_DECISION_ID_FORBIDDEN",
                "holder.prior_decision_id",
                "prior decision id requires PRIOR_DECISION_ID basis",
            )
        )

    entry_reference = result.price_references.executable_entry_reference
    invalidation = result.invalidation
    targets = result.targets
    rr = result.risk_reward
    if entry_reference.eligible and (
        entry_reference.price is None or entry_reference.timestamp is None
    ):
        issues.append(
            _issue(
                "EXECUTABLE_ENTRY_INCOMPLETE",
                "price_references.executable_entry_reference",
                "eligible entry requires price and timestamp",
            )
        )
    if entry_reference.eligible and (
        entry_reference.price != snapshot_quote.price
        or entry_reference.timestamp != snapshot_quote.latest_quote_at
        or snapshot_quote.status is not DataAvailabilityStatus.AVAILABLE
    ):
        issues.append(
            _issue(
                "EXECUTABLE_ENTRY_FACT_MISMATCH",
                "price_references.executable_entry_reference",
                "eligible entry must be the available quote fact from the bound snapshot",
            )
        )
    if entry_reference.eligible and (
        entry_reference.freshness_status
        is not result.price_references.current_price_reference.freshness_status
        or entry_reference.freshness_status is not FreshnessStatus.FRESH
    ):
        issues.append(
            _issue(
                "EXECUTABLE_ENTRY_NOT_FRESH",
                "price_references.executable_entry_reference.freshness_status",
                "eligible entry must satisfy the v1 upstream-available freshness policy",
            )
        )
    if entry_reference.eligible and (
        market_state.status is not DataAvailabilityStatus.AVAILABLE
        or market_state.canonical_state is not CanonicalMarketState.OPEN
    ):
        issues.append(
            _issue(
                "EXECUTABLE_ENTRY_MARKET_NOT_OPEN",
                "price_references.executable_entry_reference",
                "eligible entry requires an available regular-session OPEN market state",
            )
        )
    if entry_reference.eligible and (
        entry_reference.session_type is not PriceSessionType.REGULAR
        and not request.runtime_config.extended_hours_entry_reference_allowed
    ):
        issues.append(
            _issue(
                "ENTRY_SESSION_NOT_ALLOWED",
                "price_references.executable_entry_reference.session_type",
                "extended-hours entry reference is not permitted",
            )
        )
    if ready:
        expected_direction = (
            SetupDirection.LONG
            if result.entry.advisory is EntryAdvisory.LONG_READY
            else SetupDirection.SHORT
        )
        if result.setup.direction is not expected_direction:
            issues.append(
                _issue(
                    "READY_DIRECTION_MISMATCH",
                    "setup.direction",
                    "actionable advisory must match setup direction",
                )
            )
        if (
            result.support.support_status is not SupportStatus.SUPPORTED
            or result.support.input_quality is not InputQuality.COMPLETE
        ):
            issues.append(
                _issue(
                    "ACTIONABLE_INPUT_NOT_COMPLETE",
                    "support",
                    "actionable advisory requires supported, complete input",
                )
            )
        if (
            result.setup.stage is not SetupStage.CONFIRMED
            or result.price_action.trigger_status is not TriggerStatus.CONFIRMED
            or result.price_action.followthrough_status is not FollowthroughStatus.CONFIRMED
        ):
            issues.append(
                _issue(
                    "ACTIONABLE_CONFIRMATION_REQUIRED",
                    "setup",
                    "actionable advisory requires confirmed setup, trigger, and follow-through",
                )
            )
        if not entry_reference.eligible or entry_reference.price is None:
            issues.append(
                _issue(
                    "ACTIONABLE_ENTRY_REQUIRED",
                    "price_references.executable_entry_reference",
                    "actionable advisory requires an eligible entry reference",
                )
            )
        if not invalidation.level_or_zone or invalidation.calculation_reference is None:
            issues.append(
                _issue(
                    "STRUCTURAL_INVALIDATION_REQUIRED",
                    "invalidation",
                    "actionable advisory requires structural and numeric invalidation",
                )
            )
        if (
            not targets.t1_level_or_zone
            or targets.t1_calculation_reference is None
            or not targets.t1_reason.strip()
            or not targets.t1_is_nearest_structural_obstacle
        ):
            issues.append(
                _issue(
                    "NEAREST_STRUCTURAL_T1_REQUIRED",
                    "targets",
                    "actionable advisory requires the nearest structural T1",
                )
            )
        if rr.rr_status is not RRStatus.FINAL:
            issues.append(
                _issue(
                    "FINAL_RR_REQUIRED",
                    "risk_reward.rr_status",
                    "actionable advisory requires final risk/reward",
                )
            )

    if rr.rr_status is RRStatus.FINAL:
        values = (
            entry_reference.price,
            invalidation.calculation_reference,
            targets.t1_calculation_reference,
            rr.executable_entry_reference,
            rr.risk_per_share,
            rr.rr_t1,
        )
        if any(value is None for value in values) or not entry_reference.eligible:
            issues.append(
                _issue(
                    "FINAL_RR_INPUT_MISSING",
                    "risk_reward",
                    "final risk/reward requires eligible numeric references",
                )
            )
        else:
            assert entry_reference.price is not None
            assert invalidation.calculation_reference is not None
            assert targets.t1_calculation_reference is not None
            assert rr.executable_entry_reference is not None
            assert rr.risk_per_share is not None
            assert rr.rr_t1 is not None
            entry = entry_reference.price
            invalidation_reference = invalidation.calculation_reference
            t1 = targets.t1_calculation_reference
            with localcontext() as context:
                context.prec = 60
                if result.setup.direction is SetupDirection.LONG:
                    risk = entry - invalidation_reference
                    reward_t1 = t1 - entry
                elif result.setup.direction is SetupDirection.SHORT:
                    risk = invalidation_reference - entry
                    reward_t1 = entry - t1
                else:
                    risk = entry - entry
                    reward_t1 = entry - entry
                    issues.append(
                        _issue(
                            "RR_DIRECTION_INVALID",
                            "setup.direction",
                            "final risk/reward requires LONG or SHORT direction",
                        )
                    )
            if risk <= 0:
                issues.append(
                    _issue(
                        "NON_POSITIVE_RISK",
                        "risk_reward.risk_per_share",
                        "risk must be positive",
                    )
                )
            elif reward_t1 <= 0:
                issues.append(
                    _issue(
                        "TARGET_WRONG_SIDE",
                        "targets.t1_calculation_reference",
                        "T1 must be on the reward side of entry",
                    )
                )
            else:
                try:
                    expected_rr = decimal_ratio(reward_t1, risk)
                except ValueError:
                    expected_rr = None
                    issues.append(
                        _issue(
                            "RR_OUT_OF_RANGE",
                            "risk_reward.rr_t1",
                            "T1 risk/reward exceeds the exact Decimal contract",
                        )
                    )
                if rr.executable_entry_reference != entry:
                    issues.append(
                        _issue(
                            "RR_ENTRY_MISMATCH",
                            "risk_reward.executable_entry_reference",
                            "risk/reward entry must match executable reference",
                        )
                    )
                if rr.risk_per_share != risk:
                    issues.append(
                        _issue(
                            "RISK_ARITHMETIC_MISMATCH",
                            "risk_reward.risk_per_share",
                            "risk per share does not match Decimal arithmetic",
                        )
                    )
                if expected_rr is not None and rr.rr_t1 != expected_rr:
                    issues.append(
                        _issue(
                            "RR_ARITHMETIC_MISMATCH",
                            "risk_reward.rr_t1",
                            "T1 risk/reward does not match Decimal arithmetic",
                        )
                    )
                guardrails = request.runtime_config.guardrails
                if (
                    ready
                    and guardrails is not None
                    and guardrails.minimum_rr_t1 is not None
                    and expected_rr is not None
                    and expected_rr < guardrails.minimum_rr_t1
                ):
                    issues.append(
                        _issue(
                            "RR_GUARDRAIL_NOT_MET",
                            "risk_reward.rr_t1",
                            "T1 risk/reward is below the versioned runtime guardrail",
                        )
                    )
                t2 = targets.t2_calculation_reference
                if t2 is not None:
                    with localcontext() as context:
                        context.prec = 60
                        reward_t2 = (
                            t2 - entry
                            if result.setup.direction is SetupDirection.LONG
                            else entry - t2
                        )
                    if reward_t2 <= reward_t1:
                        issues.append(
                            _issue(
                                "TARGET_ORDER_INVALID",
                                "targets.t2_calculation_reference",
                                "T2 must be beyond T1 in the setup direction",
                            )
                        )
                    else:
                        try:
                            expected_rr_t2 = decimal_ratio(reward_t2, risk)
                        except ValueError:
                            issues.append(
                                _issue(
                                    "RR_OUT_OF_RANGE",
                                    "risk_reward.rr_t2",
                                    "T2 risk/reward exceeds the exact Decimal contract",
                                )
                            )
                        else:
                            if rr.rr_t2 != expected_rr_t2:
                                issues.append(
                                    _issue(
                                        "RR_T2_ARITHMETIC_MISMATCH",
                                        "risk_reward.rr_t2",
                                        "T2 risk/reward does not match Decimal arithmetic",
                                    )
                                )
                elif rr.rr_t2 is not None:
                    issues.append(
                        _issue(
                            "RR_T2_WITHOUT_TARGET",
                            "risk_reward.rr_t2",
                            "T2 risk/reward requires a numeric T2",
                        )
                    )
    elif any(
        value is not None
        for value in (
            rr.executable_entry_reference,
            rr.risk_per_share,
            rr.rr_t1,
            rr.rr_t2,
        )
    ):
        issues.append(
            _issue(
                "NON_FINAL_RR_MUST_BE_EMPTY",
                "risk_reward",
                "non-final risk/reward must not contain calculated values",
            )
        )

    if issues:
        return PaqsEValidationFailure(
            validator_version=PAQS_E_VALIDATOR_VERSION,
            issues=tuple(issues),
        )
    return ValidatedPaqsEResult(
        validator_version=PAQS_E_VALIDATOR_VERSION,
        provider_response_id=provider_response_id,
        result=result,
    )


@dataclass(frozen=True, slots=True)
class PaqsEReasoningRuntime:
    provider: PaqsEReasoningProvider

    def reason(
        self,
        *,
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
    ) -> ValidatedPaqsEResult | PaqsEValidationFailure | ReasoningProviderFailure:
        if strategy.strategy_id != request.primary_strategy_id or (
            strategy.content_sha256 != request.primary_strategy_content_sha256
        ):
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="strategy package does not match request identity",
            )
        if _sha256(strategy.content.encode("utf-8")) != strategy.content_sha256:
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="strategy package content does not match its SHA-256",
            )
        if prompt.prompt_version != request.prompt_version or (
            prompt.content_sha256 != request.prompt_content_sha256
        ):
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="prompt package does not match request identity",
            )
        if _sha256(prompt.content.encode("utf-8")) != prompt.content_sha256:
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="prompt package content does not match its SHA-256",
            )
        outcome: ReasoningProviderOutcome = self.provider.reason(
            request=request,
            strategy=strategy,
            prompt=prompt,
        )
        if isinstance(outcome, ReasoningProviderFailure):
            return outcome
        if not isinstance(outcome, ReasoningProviderSuccess):
            raise TypeError("reasoning provider returned an unsupported outcome")
        return validate_reasoning_result(
            request=request,
            result=project_snapshot_price_facts(request=request, result=outcome.result),
            provider_response_id=outcome.provider_response_id,
        )


def project_snapshot_price_facts(
    *, request: PaqsEReasoningRequestV1, result: PaqsEReasoningResultV1
) -> PaqsEReasoningResultV1:
    """Project factual echoes after strict parsing, before the unchanged validator.

    These mappings mirror the accepted validator. No semantic assessment, eligibility,
    policy text, identity, invalidation, target or RR field is corrected here.
    """
    quote = request.market_snapshot.current_price_reference
    market = request.market_snapshot.market_state_reference
    freshness = {
        DataAvailabilityStatus.AVAILABLE: FreshnessStatus.FRESH,
        DataAvailabilityStatus.STALE: FreshnessStatus.STALE,
        DataAvailabilityStatus.DELAYED: FreshnessStatus.DELAYED,
    }.get(quote.status, FreshnessStatus.UNKNOWN)
    session = {
        None: PriceSessionType.UNKNOWN,
        CanonicalMarketState.OPEN: PriceSessionType.REGULAR,
        CanonicalMarketState.PRE_MARKET: PriceSessionType.PRE,
        CanonicalMarketState.AFTER_HOURS: PriceSessionType.POST,
        CanonicalMarketState.CLOSED: PriceSessionType.CLOSED_REFERENCE,
    }.get(market.canonical_state, PriceSessionType.UNKNOWN)
    references = result.price_references
    current = replace(
        references.current_price_reference,
        price=quote.price,
        timestamp=quote.latest_quote_at,
        freshness_status=freshness,
        session_type=session,
    )
    entry = references.executable_entry_reference
    if entry.eligible:
        entry = replace(
            entry,
            price=current.price,
            timestamp=current.timestamp,
            freshness_status=current.freshness_status,
            session_type=current.session_type,
        )
    return replace(
        result,
        price_references=replace(
            references, current_price_reference=current, executable_entry_reference=entry
        ),
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, DecimalException, localcontext
from enum import StrEnum

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.enums import InstrumentType
from ai_infra_quant.core.domain.money import parse_decimal
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot

PAQS_E_REQUEST_SCHEMA_VERSION = "paqs-e-reasoning-request-v1"
PAQS_E_OUTPUT_SCHEMA_VERSION = "paqs-e-reasoning-result-v1"
PAQS_E_RUNTIME_CONFIG_VERSION = "paqs-e-runtime-config-v1"
PAQS_E_PROMPT_VERSION = "paqs-e-runtime-prompt-v1"
PAQS_E_VALIDATOR_VERSION = "paqs-e-validator-v1"
OPENAI_PROVIDER_ID = "openai"
PAQS_E_DEFAULT_STRATEGY_ID = "paqs-e-master"
PAQS_E_ENTRY_REFERENCE_POLICY_V1 = "SNAPSHOT_QUOTE_REGULAR_OPEN_REQUIRED"
PAQS_E_QUOTE_FRESHNESS_POLICY_V1 = "UPSTREAM_AVAILABLE_REQUIRED"


class AnalysisMode(StrEnum):
    CURRENT_ANALYSIS = "CURRENT_ANALYSIS"
    HISTORICAL_ASOF_REPLAY = "HISTORICAL_ASOF_REPLAY"


class SupportStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


class InputQuality(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INVALID = "INVALID"


class ContextState(StrEnum):
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    RANGE = "RANGE"
    TRANSITION = "TRANSITION"
    REVERSAL_CANDIDATE = "REVERSAL_CANDIDATE"
    TREND_DETERIORATING = "TREND_DETERIORATING"
    UNCERTAIN = "UNCERTAIN"


class MarketBias(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNCERTAIN = "UNCERTAIN"


class LocationQuality(StrEnum):
    GOOD = "GOOD"
    MARGINAL = "MARGINAL"
    POOR = "POOR"


class EventType(StrEnum):
    CORRECTION = "CORRECTION"
    BREAK_ATTEMPT = "BREAK_ATTEMPT"
    ACCEPTED_BREAKOUT = "ACCEPTED_BREAKOUT"
    FAILED_BREAKOUT = "FAILED_BREAKOUT"
    RECLAIM = "RECLAIM"
    RETEST = "RETEST"
    ROLE_FLIP = "ROLE_FLIP"
    TREND_DETERIORATION = "TREND_DETERIORATION"
    EXHAUSTION_CANDIDATE = "EXHAUSTION_CANDIDATE"
    NONE = "NONE"


class TriggerStatus(StrEnum):
    NOT_CONFIRMED = "NOT_CONFIRMED"
    CONFIRMED = "CONFIRMED"
    UNAVAILABLE = "UNAVAILABLE"


class FollowthroughStatus(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    WEAK = "WEAK"
    CONFIRMED = "CONFIRMED"
    UNAVAILABLE = "UNAVAILABLE"


class SetupFamily(StrEnum):
    A_TREND_PULLBACK_CONTINUATION = "A_TREND_PULLBACK_CONTINUATION"
    B_FAILED_BREAKOUT_REVERSAL = "B_FAILED_BREAKOUT_REVERSAL"
    C_RIGHT_SIDE_STRUCTURAL_BREAKOUT = "C_RIGHT_SIDE_STRUCTURAL_BREAKOUT"
    NONE = "NONE"


class SetupDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class SetupStage(StrEnum):
    NONE = "NONE"
    CANDIDATE = "CANDIDATE"
    TRIGGER_PENDING = "TRIGGER_PENDING"
    FOLLOWTHROUGH_PENDING = "FOLLOWTHROUGH_PENDING"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"


class SetupExpiryReason(StrEnum):
    PRICE_EXTENDED_OPPORTUNITY_MISSED = "PRICE_EXTENDED_OPPORTUNITY_MISSED"
    SETUP_GEOMETRY_REPLACED = "SETUP_GEOMETRY_REPLACED"
    STRUCTURE_INVALIDATED = "STRUCTURE_INVALIDATED"
    RUNTIME_CONFIG_EXPIRY = "RUNTIME_CONFIG_EXPIRY"


class EntryAdvisory(StrEnum):
    NO_SETUP = "NO_SETUP"
    WATCH_LONG = "WATCH_LONG"
    WATCH_SHORT = "WATCH_SHORT"
    ENTRY_PENDING_REVALIDATION = "ENTRY_PENDING_REVALIDATION"
    LONG_READY = "LONG_READY"
    SHORT_READY = "SHORT_READY"
    VALID_SETUP_BUT_POOR_ENTRY = "VALID_SETUP_BUT_POOR_ENTRY"
    WAIT_RETEST = "WAIT_RETEST"
    NO_TRADE = "NO_TRADE"
    SETUP_EXPIRED = "SETUP_EXPIRED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    UNCERTAIN = "UNCERTAIN"


class HolderAdvisoryBasis(StrEnum):
    CURRENT_ANALYSIS_THESIS = "CURRENT_ANALYSIS_THESIS"
    PRIOR_DECISION_ID = "PRIOR_DECISION_ID"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class HolderAdvisory(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    THESIS_VALID = "THESIS_VALID"
    HOLD_WITH_WARNING = "HOLD_WITH_WARNING"
    TARGET_REACHED_REVIEW = "TARGET_REACHED_REVIEW"
    EXIT_IF_HELD = "EXIT_IF_HELD"
    UNCERTAIN = "UNCERTAIN"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


class RRStatus(StrEnum):
    FINAL = "FINAL"
    PENDING_ENTRY_REFERENCE = "PENDING_ENTRY_REFERENCE"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"


class ChaseRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UncertaintyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InvalidationStrength(StrEnum):
    HARD = "HARD"
    SOFT = "SOFT"


class PriceSessionType(StrEnum):
    REGULAR = "REGULAR"
    PRE = "PRE"
    POST = "POST"
    CLOSED_REFERENCE = "CLOSED_REFERENCE"
    UNKNOWN = "UNKNOWN"


class FreshnessStatus(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    DELAYED = "DELAYED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PaqsERuntimeGuardrails:
    version: str
    minimum_rr_t1: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("guardrail version is required")
        if self.minimum_rr_t1 is not None:
            parsed = parse_decimal(self.minimum_rr_t1)
            if parsed < 0:
                raise ValueError("minimum_rr_t1 cannot be negative")
            object.__setattr__(self, "minimum_rr_t1", parsed)


@dataclass(frozen=True, slots=True)
class PaqsERuntimeConfigV1:
    runtime_config_version: str = PAQS_E_RUNTIME_CONFIG_VERSION
    supported_market_scope: tuple[str, ...] = ("US", "HK")
    supported_instrument_scope: tuple[InstrumentType, ...] = (InstrumentType.EQUITY,)
    htf: str = "W1"
    stf: str = "D1"
    ttf: str = "M30_REGULAR"
    short_advisory_allowed: bool = True
    short_execution_allowed: bool = False
    extended_hours_entry_reference_allowed: bool = False
    entry_reference_policy: str = PAQS_E_ENTRY_REFERENCE_POLICY_V1
    quote_freshness_policy: str = PAQS_E_QUOTE_FRESHNESS_POLICY_V1
    guardrails: PaqsERuntimeGuardrails | None = None

    def __post_init__(self) -> None:
        if self.runtime_config_version != PAQS_E_RUNTIME_CONFIG_VERSION:
            raise ValueError("unsupported PAQS-E runtime configuration version")
        if self.supported_market_scope != ("US", "HK"):
            raise ValueError("v1 PAQS-E market scope must be US/HK")
        if self.supported_instrument_scope != (InstrumentType.EQUITY,):
            raise ValueError("v1 PAQS-E instrument scope must be EQUITY")
        if (self.htf, self.stf, self.ttf) != ("W1", "D1", "M30_REGULAR"):
            raise ValueError("v1 PAQS-E timeframe policy is fixed")
        if not self.short_advisory_allowed or self.short_execution_allowed:
            raise ValueError("v1 allows short advisory but not actionable short execution")
        if self.extended_hours_entry_reference_allowed:
            raise ValueError("v1 does not allow extended-hours entry references")
        if self.entry_reference_policy != PAQS_E_ENTRY_REFERENCE_POLICY_V1:
            raise ValueError("unsupported v1 entry reference policy")
        if self.quote_freshness_policy != PAQS_E_QUOTE_FRESHNESS_POLICY_V1:
            raise ValueError("unsupported v1 quote freshness policy")


@dataclass(frozen=True, slots=True)
class AuxiliaryContextItem:
    context_id: str
    category: str
    source_label: str
    source_timestamp: datetime | None
    provenance: str | None
    as_of_compatible: bool
    content: str

    def __post_init__(self) -> None:
        for name in ("context_id", "category", "source_label", "content"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.source_timestamp is not None:
            object.__setattr__(self, "source_timestamp", require_utc(self.source_timestamp))


@dataclass(frozen=True, slots=True)
class StrategyPackage:
    strategy_id: str
    display_name: str
    source_path: str
    content_sha256: str
    content: str


@dataclass(frozen=True, slots=True)
class PromptPackage:
    prompt_version: str
    source_path: str
    content_sha256: str
    content: str


@dataclass(frozen=True, slots=True)
class PaqsEReasoningRequestV1:
    request_schema_version: str
    snapshot_hash: str
    symbol: str
    market: str
    instrument_type: InstrumentType
    snapshot_as_of_timestamp: datetime
    analysis_mode: AnalysisMode
    runtime_config_version: str
    prompt_version: str
    prompt_content_sha256: str
    output_schema_version: str
    model_provider: str
    model_id: str
    primary_strategy_id: str
    primary_strategy_content_sha256: str
    runtime_config: PaqsERuntimeConfigV1
    market_snapshot: PaqsMarketSnapshot
    auxiliary_context: tuple[AuxiliaryContextItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_as_of_timestamp",
            require_utc(self.snapshot_as_of_timestamp),
        )
        if self.request_schema_version != PAQS_E_REQUEST_SCHEMA_VERSION:
            raise ValueError("unsupported PAQS-E request schema version")
        if self.output_schema_version != PAQS_E_OUTPUT_SCHEMA_VERSION:
            raise ValueError("unsupported PAQS-E output schema version")
        if self.analysis_mode is not AnalysisMode.CURRENT_ANALYSIS:
            raise ValueError("TASK-007A supports current analysis only")
        if self.runtime_config_version != self.runtime_config.runtime_config_version:
            raise ValueError("runtime configuration identity mismatch")
        if self.market != self.market_snapshot.security.market:
            raise ValueError("request market does not match snapshot")
        if self.symbol != self.market_snapshot.security.symbol:
            raise ValueError("request symbol does not match snapshot")
        if self.instrument_type is not self.market_snapshot.security.instrument_type:
            raise ValueError("request instrument type does not match snapshot")
        if self.snapshot_hash != self.market_snapshot.snapshot_hash:
            raise ValueError("request snapshot hash does not match snapshot")
        if self.snapshot_as_of_timestamp != self.market_snapshot.as_of_timestamp:
            raise ValueError("request As-Of does not match snapshot")
        if self.market not in self.runtime_config.supported_market_scope:
            raise ValueError("request market is outside runtime scope")
        if self.instrument_type not in self.runtime_config.supported_instrument_scope:
            raise ValueError("request instrument is outside runtime scope")
        for name in (
            "prompt_version",
            "model_provider",
            "model_id",
            "primary_strategy_id",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        for name in ("prompt_content_sha256", "primary_strategy_content_sha256"):
            value = getattr(self, name)
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError(f"{name} must be a lowercase SHA-256")
        for item in self.auxiliary_context:
            if not item.as_of_compatible:
                raise ValueError(
                    "TASK-007A CURRENT_ANALYSIS rejects As-Of-incompatible auxiliary context"
                )
            if (
                item.source_timestamp is not None
                and item.source_timestamp > self.snapshot_as_of_timestamp
            ):
                raise ValueError("As-Of-compatible auxiliary context cannot come from the future")
        context_ids = [item.context_id for item in self.auxiliary_context]
        if len(context_ids) != len(set(context_ids)):
            raise ValueError("auxiliary context ids must be unique")


@dataclass(frozen=True, slots=True)
class ResultIdentity:
    request_schema_version: str
    output_schema_version: str
    snapshot_hash: str
    symbol: str
    market: str
    instrument_type: InstrumentType
    snapshot_as_of_timestamp: datetime
    analysis_mode: AnalysisMode
    runtime_config_version: str
    prompt_version: str
    prompt_content_sha256: str
    model_provider: str
    model_id: str
    primary_strategy_id: str
    primary_strategy_content_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_as_of_timestamp",
            require_utc(self.snapshot_as_of_timestamp),
        )


@dataclass(frozen=True, slots=True)
class SupportAssessment:
    support_status: SupportStatus
    input_quality: InputQuality
    data_quality_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TimeframeContext:
    states: tuple[ContextState, ...]
    evidence: str

    def __post_init__(self) -> None:
        if len(self.states) > len(ContextState) or len(self.states) != len(set(self.states)):
            raise ValueError("timeframe context states must be a bounded unique set")


@dataclass(frozen=True, slots=True)
class ContextAssessment:
    htf: TimeframeContext
    stf: TimeframeContext
    ttf: TimeframeContext
    regime_summary: str
    trend_quality: str
    market_bias: MarketBias
    avoid_long_flag: bool


@dataclass(frozen=True, slots=True)
class KeyLevel:
    price_or_zone: str
    role: str
    timeframe: str
    rationale: str
    state_change: str


@dataclass(frozen=True, slots=True)
class CurrentLocation:
    description: str
    quality: LocationQuality | None


@dataclass(frozen=True, slots=True)
class PriceActionAssessment:
    current_event: EventType
    transition_states: tuple[ContextState, ...]
    trigger_status: TriggerStatus
    followthrough_status: FollowthroughStatus
    impulse_correction_read: str
    channel_or_exhaustion_context: str | None
    structural_confirmation_uses_reference_only_quote: bool

    def __post_init__(self) -> None:
        if len(self.transition_states) > len(ContextState) or len(self.transition_states) != len(
            set(self.transition_states)
        ):
            raise ValueError("transition states must be a bounded unique set")


@dataclass(frozen=True, slots=True)
class SetupAssessment:
    family: SetupFamily
    direction: SetupDirection
    stage: SetupStage
    expiry_reason: SetupExpiryReason | None
    why_it_qualifies: str
    missing_confirmation: tuple[str, ...]
    alternative_interpretation: str


@dataclass(frozen=True, slots=True)
class CurrentPriceOutput:
    price: Decimal | None
    timestamp: datetime | None
    session_type: PriceSessionType
    freshness_status: FreshnessStatus

    def __post_init__(self) -> None:
        if self.price is not None:
            object.__setattr__(self, "price", parse_decimal(self.price))
        if self.timestamp is not None:
            object.__setattr__(self, "timestamp", require_utc(self.timestamp))


@dataclass(frozen=True, slots=True)
class ExecutableEntryOutput:
    price: Decimal | None
    timestamp: datetime | None
    session_type: PriceSessionType
    freshness_status: FreshnessStatus
    policy_basis: str
    eligible: bool

    def __post_init__(self) -> None:
        if self.price is not None:
            object.__setattr__(self, "price", parse_decimal(self.price))
        if self.timestamp is not None:
            object.__setattr__(self, "timestamp", require_utc(self.timestamp))
        if not self.policy_basis.strip():
            raise ValueError("executable entry policy basis is required")


@dataclass(frozen=True, slots=True)
class PriceReferences:
    current_price_reference: CurrentPriceOutput
    executable_entry_reference: ExecutableEntryOutput


@dataclass(frozen=True, slots=True)
class EntryAssessment:
    advisory: EntryAdvisory
    reference_or_zone: str | None
    chase_risk: ChaseRisk
    wait_condition: str


@dataclass(frozen=True, slots=True)
class InvalidationAssessment:
    level_or_zone: str | None
    calculation_reference: Decimal | None
    condition: str
    timeframe: str
    reason: str
    strength: InvalidationStrength

    def __post_init__(self) -> None:
        if self.calculation_reference is not None:
            object.__setattr__(
                self,
                "calculation_reference",
                parse_decimal(self.calculation_reference),
            )


@dataclass(frozen=True, slots=True)
class TargetsAssessment:
    t1_level_or_zone: str | None
    t1_calculation_reference: Decimal | None
    t1_reason: str
    t1_is_nearest_structural_obstacle: bool
    t2_level_or_zone: str | None
    t2_calculation_reference: Decimal | None
    t2_reason: str | None

    def __post_init__(self) -> None:
        for name in ("t1_calculation_reference", "t2_calculation_reference"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, parse_decimal(value))


@dataclass(frozen=True, slots=True)
class RiskRewardAssessment:
    rr_status: RRStatus
    executable_entry_reference: Decimal | None
    risk_per_share: Decimal | None
    rr_t1: Decimal | None
    rr_t2: Decimal | None
    rr_quality: str

    def __post_init__(self) -> None:
        for name in (
            "executable_entry_reference",
            "risk_per_share",
            "rr_t1",
            "rr_t2",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, parse_decimal(value))


@dataclass(frozen=True, slots=True)
class HolderAssessment:
    advisory_basis: HolderAdvisoryBasis
    prior_decision_id: str | None
    advisory: HolderAdvisory


@dataclass(frozen=True, slots=True)
class UncertaintyAssessment:
    level: UncertaintyLevel
    conflicting_evidence: tuple[str, ...]
    data_limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PaqsEReasoningResultV1:
    identity: ResultIdentity
    support: SupportAssessment
    one_line_thesis: str
    context: ContextAssessment
    key_levels: tuple[KeyLevel, ...]
    current_location: CurrentLocation
    price_action: PriceActionAssessment
    setup: SetupAssessment
    price_references: PriceReferences
    entry: EntryAssessment
    invalidation: InvalidationAssessment
    targets: TargetsAssessment
    risk_reward: RiskRewardAssessment
    holder: HolderAssessment
    uncertainty: UncertaintyAssessment
    next_evidence_needed: tuple[str, ...]
    reason_codes: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if len(self.key_levels) > 4:
            raise ValueError("at most four current decision-relevant key levels are allowed")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidatedPaqsEResult:
    validator_version: str
    provider_response_id: str | None
    result: PaqsEReasoningResultV1


@dataclass(frozen=True, slots=True)
class PaqsEValidationFailure:
    validator_version: str
    issues: tuple[ValidationIssue, ...]


def decimal_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Return a deterministic scale-18 ratio for validator comparisons."""
    numerator = parse_decimal(numerator)
    denominator = parse_decimal(denominator)
    if denominator <= 0:
        raise ValueError("ratio denominator must be positive")
    try:
        with localcontext() as context:
            context.prec = 60
            value = (numerator / denominator).quantize(
                Decimal("0.000000000000000001"),
                rounding=ROUND_HALF_EVEN,
            )
    except DecimalException as exc:
        raise ValueError("ratio exceeds deterministic Decimal bounds") from exc
    return parse_decimal(value)

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ai_infra_quant.core.domain.enums import InstrumentType
from ai_infra_quant.core.domain.money import parse_decimal
from ai_infra_quant.core.domain.paqs_e_reasoning import (
    AnalysisMode,
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
    PaqsEReasoningResultV1,
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
)

CanonicalDecimal = Annotated[
    str,
    StringConstraints(pattern=r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class StrictOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ResultIdentitySchema(StrictOutputModel):
    request_schema_version: str
    output_schema_version: str
    snapshot_hash: Sha256
    symbol: str
    market: str
    instrument_type: InstrumentType
    snapshot_as_of_timestamp: datetime
    analysis_mode: AnalysisMode
    runtime_config_version: str
    prompt_version: str
    prompt_content_sha256: Sha256
    model_provider: str
    model_id: str
    primary_strategy_id: str
    primary_strategy_content_sha256: Sha256


class SupportAssessmentSchema(StrictOutputModel):
    support_status: SupportStatus
    input_quality: InputQuality
    data_quality_reasons: list[str]


class TimeframeContextSchema(StrictOutputModel):
    states: list[ContextState] = Field(max_length=len(ContextState))
    evidence: str


class ContextAssessmentSchema(StrictOutputModel):
    htf: TimeframeContextSchema
    stf: TimeframeContextSchema
    ttf: TimeframeContextSchema
    regime_summary: str
    trend_quality: str
    market_bias: MarketBias
    avoid_long_flag: bool


class KeyLevelSchema(StrictOutputModel):
    price_or_zone: str
    role: str
    timeframe: str
    rationale: str
    state_change: str


class CurrentLocationSchema(StrictOutputModel):
    description: str
    quality: LocationQuality | None


class PriceActionAssessmentSchema(StrictOutputModel):
    current_event: EventType
    transition_states: list[ContextState] = Field(max_length=len(ContextState))
    trigger_status: TriggerStatus
    followthrough_status: FollowthroughStatus
    impulse_correction_read: str
    channel_or_exhaustion_context: str | None
    structural_confirmation_uses_reference_only_quote: bool


class SetupAssessmentSchema(StrictOutputModel):
    family: SetupFamily
    direction: SetupDirection
    stage: SetupStage
    expiry_reason: SetupExpiryReason | None
    why_it_qualifies: str
    missing_confirmation: list[str]
    alternative_interpretation: str


class CurrentPriceOutputSchema(StrictOutputModel):
    price: CanonicalDecimal | None
    timestamp: datetime | None
    session_type: PriceSessionType
    freshness_status: FreshnessStatus


class ExecutableEntryOutputSchema(StrictOutputModel):
    price: CanonicalDecimal | None
    timestamp: datetime | None
    session_type: PriceSessionType
    freshness_status: FreshnessStatus
    policy_basis: str
    eligible: bool


class PriceReferencesSchema(StrictOutputModel):
    current_price_reference: CurrentPriceOutputSchema
    executable_entry_reference: ExecutableEntryOutputSchema


class EntryAssessmentSchema(StrictOutputModel):
    advisory: EntryAdvisory
    reference_or_zone: str | None
    chase_risk: ChaseRisk
    wait_condition: str


class InvalidationAssessmentSchema(StrictOutputModel):
    level_or_zone: str | None
    calculation_reference: CanonicalDecimal | None
    condition: str
    timeframe: str
    reason: str
    strength: InvalidationStrength


class TargetsAssessmentSchema(StrictOutputModel):
    t1_level_or_zone: str | None
    t1_calculation_reference: CanonicalDecimal | None
    t1_reason: str
    t1_is_nearest_structural_obstacle: bool
    t2_level_or_zone: str | None
    t2_calculation_reference: CanonicalDecimal | None
    t2_reason: str | None


class RiskRewardAssessmentSchema(StrictOutputModel):
    rr_status: RRStatus
    executable_entry_reference: CanonicalDecimal | None
    risk_per_share: CanonicalDecimal | None
    rr_t1: CanonicalDecimal | None
    rr_t2: CanonicalDecimal | None
    rr_quality: str


class HolderAssessmentSchema(StrictOutputModel):
    advisory_basis: HolderAdvisoryBasis
    prior_decision_id: str | None
    advisory: HolderAdvisory


class UncertaintyAssessmentSchema(StrictOutputModel):
    level: UncertaintyLevel
    conflicting_evidence: list[str]
    data_limitations: list[str]


class PaqsEReasoningResultSchemaV1(StrictOutputModel):
    identity: ResultIdentitySchema
    support: SupportAssessmentSchema
    one_line_thesis: str
    context: ContextAssessmentSchema
    key_levels: list[KeyLevelSchema] = Field(max_length=4)
    current_location: CurrentLocationSchema
    price_action: PriceActionAssessmentSchema
    setup: SetupAssessmentSchema
    price_references: PriceReferencesSchema
    entry: EntryAssessmentSchema
    invalidation: InvalidationAssessmentSchema
    targets: TargetsAssessmentSchema
    risk_reward: RiskRewardAssessmentSchema
    holder: HolderAssessmentSchema
    uncertainty: UncertaintyAssessmentSchema
    next_evidence_needed: list[str]
    reason_codes: list[str]
    explanation: str

    def to_domain(self) -> PaqsEReasoningResultV1:
        identity = self.identity
        context = self.context
        price_action = self.price_action
        setup = self.setup
        current_price = self.price_references.current_price_reference
        executable_entry = self.price_references.executable_entry_reference
        invalidation = self.invalidation
        targets = self.targets
        rr = self.risk_reward
        return PaqsEReasoningResultV1(
            identity=ResultIdentity(**identity.model_dump()),
            support=SupportAssessment(
                support_status=self.support.support_status,
                input_quality=self.support.input_quality,
                data_quality_reasons=tuple(self.support.data_quality_reasons),
            ),
            one_line_thesis=self.one_line_thesis,
            context=ContextAssessment(
                htf=TimeframeContext(
                    states=tuple(context.htf.states), evidence=context.htf.evidence
                ),
                stf=TimeframeContext(
                    states=tuple(context.stf.states), evidence=context.stf.evidence
                ),
                ttf=TimeframeContext(
                    states=tuple(context.ttf.states), evidence=context.ttf.evidence
                ),
                regime_summary=context.regime_summary,
                trend_quality=context.trend_quality,
                market_bias=context.market_bias,
                avoid_long_flag=context.avoid_long_flag,
            ),
            key_levels=tuple(KeyLevel(**level.model_dump()) for level in self.key_levels),
            current_location=CurrentLocation(**self.current_location.model_dump()),
            price_action=PriceActionAssessment(
                current_event=price_action.current_event,
                transition_states=tuple(price_action.transition_states),
                trigger_status=price_action.trigger_status,
                followthrough_status=price_action.followthrough_status,
                impulse_correction_read=price_action.impulse_correction_read,
                channel_or_exhaustion_context=price_action.channel_or_exhaustion_context,
                structural_confirmation_uses_reference_only_quote=(
                    price_action.structural_confirmation_uses_reference_only_quote
                ),
            ),
            setup=SetupAssessment(
                family=setup.family,
                direction=setup.direction,
                stage=setup.stage,
                expiry_reason=setup.expiry_reason,
                why_it_qualifies=setup.why_it_qualifies,
                missing_confirmation=tuple(setup.missing_confirmation),
                alternative_interpretation=setup.alternative_interpretation,
            ),
            price_references=PriceReferences(
                current_price_reference=CurrentPriceOutput(
                    price=None
                    if current_price.price is None
                    else parse_decimal(current_price.price),
                    timestamp=current_price.timestamp,
                    session_type=current_price.session_type,
                    freshness_status=current_price.freshness_status,
                ),
                executable_entry_reference=ExecutableEntryOutput(
                    price=(
                        None
                        if executable_entry.price is None
                        else parse_decimal(executable_entry.price)
                    ),
                    timestamp=executable_entry.timestamp,
                    session_type=executable_entry.session_type,
                    freshness_status=executable_entry.freshness_status,
                    policy_basis=executable_entry.policy_basis,
                    eligible=executable_entry.eligible,
                ),
            ),
            entry=EntryAssessment(**self.entry.model_dump()),
            invalidation=InvalidationAssessment(
                level_or_zone=invalidation.level_or_zone,
                calculation_reference=(
                    None
                    if invalidation.calculation_reference is None
                    else parse_decimal(invalidation.calculation_reference)
                ),
                condition=invalidation.condition,
                timeframe=invalidation.timeframe,
                reason=invalidation.reason,
                strength=invalidation.strength,
            ),
            targets=TargetsAssessment(
                t1_level_or_zone=targets.t1_level_or_zone,
                t1_calculation_reference=(
                    None
                    if targets.t1_calculation_reference is None
                    else parse_decimal(targets.t1_calculation_reference)
                ),
                t1_reason=targets.t1_reason,
                t1_is_nearest_structural_obstacle=targets.t1_is_nearest_structural_obstacle,
                t2_level_or_zone=targets.t2_level_or_zone,
                t2_calculation_reference=(
                    None
                    if targets.t2_calculation_reference is None
                    else parse_decimal(targets.t2_calculation_reference)
                ),
                t2_reason=targets.t2_reason,
            ),
            risk_reward=RiskRewardAssessment(
                rr_status=rr.rr_status,
                executable_entry_reference=(
                    None
                    if rr.executable_entry_reference is None
                    else parse_decimal(rr.executable_entry_reference)
                ),
                risk_per_share=(
                    None if rr.risk_per_share is None else parse_decimal(rr.risk_per_share)
                ),
                rr_t1=None if rr.rr_t1 is None else parse_decimal(rr.rr_t1),
                rr_t2=None if rr.rr_t2 is None else parse_decimal(rr.rr_t2),
                rr_quality=rr.rr_quality,
            ),
            holder=HolderAssessment(**self.holder.model_dump()),
            uncertainty=UncertaintyAssessment(
                level=self.uncertainty.level,
                conflicting_evidence=tuple(self.uncertainty.conflicting_evidence),
                data_limitations=tuple(self.uncertainty.data_limitations),
            ),
            next_evidence_needed=tuple(self.next_evidence_needed),
            reason_codes=tuple(self.reason_codes),
            explanation=self.explanation,
        )

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ai_infra_quant.core.domain.common import canonical_uuid
from ai_infra_quant.core.domain.enums import DataAvailabilityStatus, ScoreCoverageStatus


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    id: str
    name: str
    version: str
    implementation_key: str
    research_status: str
    enabled: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", canonical_uuid(self.id))


@dataclass(frozen=True, slots=True)
class HistoryRequirement:
    completed_sessions: int


@dataclass(frozen=True, slots=True)
class StrategyContext:
    security_id: str
    data_as_of: datetime
    values: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class IndicatorSet:
    values: Mapping[str, Decimal | None]


@dataclass(frozen=True, slots=True)
class ScoreResult:
    score: Decimal | None
    status: ScoreCoverageStatus
    missing_components: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SignalResult:
    signal: str
    status: DataAvailabilityStatus


@dataclass(frozen=True, slots=True)
class SignalExplanation:
    reason_codes: tuple[str, ...]


class Strategy(ABC):
    """Canonical strategy contract only; no Phase 1 implementation exists."""

    name: str
    version: str

    @abstractmethod
    def required_history(self) -> HistoryRequirement: ...

    @abstractmethod
    def calculate_indicators(self, context: StrategyContext) -> IndicatorSet: ...

    @abstractmethod
    def calculate_score(self, context: StrategyContext) -> ScoreResult: ...

    @abstractmethod
    def generate_signal(self, context: StrategyContext) -> SignalResult: ...

    @abstractmethod
    def explain_signal(self, context: StrategyContext) -> SignalExplanation: ...

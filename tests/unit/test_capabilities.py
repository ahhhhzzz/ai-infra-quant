from ai_infra_quant.core.domain.enums import (
    CapabilityStatus,
    DataAvailabilityStatus,
    ScoreCoverageStatus,
    SnapshotQualityStatus,
)
from ai_infra_quant.core.domain.providers import CapabilityItem, CapabilitySet


def test_capability_and_data_statuses_are_distinct() -> None:
    capabilities = CapabilitySet(
        (CapabilityItem("MARKET_ORDER", CapabilityStatus.NOT_IMPLEMENTED, "Phase 2"),)
    )
    assert capabilities.items[0].status is CapabilityStatus.NOT_IMPLEMENTED
    assert DataAvailabilityStatus.UNAVAILABLE.value == "UNAVAILABLE"
    assert SnapshotQualityStatus.COMPLETE.value == "COMPLETE"
    assert ScoreCoverageStatus.PARTIAL.value == "PARTIAL"
    assert len({CapabilityStatus.NOT_SUPPORTED.value, CapabilityStatus.NOT_IMPLEMENTED.value}) == 2

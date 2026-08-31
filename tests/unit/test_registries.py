import pytest

from ai_infra_quant.core.domain.enums import CapabilityStatus
from ai_infra_quant.core.domain.providers import AdapterDescriptor
from ai_infra_quant.integrations.descriptors import build_phase_one_registries


def test_registries_are_independent_and_inert() -> None:
    registries = build_phase_one_registries()
    assert registries.brokers.get("paper") is not None
    assert registries.market_data.get("paper") is None
    assert registries.market_data.get("none") is not None
    assert id(registries.fundamental_data) != id(registries.market_data)
    assert id(registries.event_data) != id(registries.fundamental_data)
    assert registries.brokers.get("futu").connection_status is CapabilityStatus.UNAVAILABLE  # type: ignore[union-attr]


def test_duplicate_descriptor_is_rejected() -> None:
    registries = build_phase_one_registries()
    with pytest.raises(ValueError, match="already registered"):
        registries.market_data.register(
            AdapterDescriptor(
                name="none",
                implementation_status=CapabilityStatus.UNAVAILABLE,
                connection_status=CapabilityStatus.UNAVAILABLE,
                environment=None,
                message="duplicate",
            )
        )

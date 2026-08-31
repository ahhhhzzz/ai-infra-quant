from ai_infra_quant.backend.schemas.common import StrictSchema
from ai_infra_quant.core.domain.enums import CapabilityStatus, DataAvailabilityStatus


class CapabilityRead(StrictSchema):
    name: str
    status: CapabilityStatus
    reason: str | None


class AdapterStatusRead(StrictSchema):
    name: str
    implementation_status: CapabilityStatus
    connection_status: CapabilityStatus
    environment: str | None
    last_checked_at: str | None = None
    message: str
    capabilities: list[CapabilityRead]


class AdapterListRead(StrictSchema):
    items: list[AdapterStatusRead]


class StrategyDefinitionRead(StrictSchema):
    id: str
    name: str
    version: str
    implementation_status: CapabilityStatus
    research_status: str
    enabled: bool
    required_data_status: DataAvailabilityStatus

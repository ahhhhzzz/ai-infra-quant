from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ai_infra_quant.core.domain.enums import DataAvailabilityStatus


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataValue(StrictSchema):
    value: str | None
    status: DataAvailabilityStatus
    as_of: str | None = None
    source: str | None = None
    reason: str | None = None


class Page[ItemT](StrictSchema):
    items: list[ItemT]
    next_cursor: str | None = None
    has_more: bool = False


class ValidationEntry(StrictSchema):
    field: str
    code: str
    message: str


class Problem(StrictSchema):
    type: str
    title: str
    status: int
    code: str
    detail: str
    instance: str
    request_id: str
    errors: list[ValidationEntry] = Field(default_factory=list)

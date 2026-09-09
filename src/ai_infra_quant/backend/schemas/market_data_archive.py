"""Bounded explicit archive request; provider, range and mode are server-owned."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArchiveCaptureCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    security_id: UUID

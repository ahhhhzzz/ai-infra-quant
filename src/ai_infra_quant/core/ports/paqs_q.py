"""Replaceable versioned pure plugins. Acquisition and persistence are not ports here."""

from typing import Protocol

from ai_infra_quant.core.domain.paqs_q.inputs import QInput
from ai_infra_quant.core.domain.paqs_q.results import Config, Descriptor, QResult


class StructurePlugin(Protocol):
    @property
    def descriptor(self) -> Descriptor: ...

    def resolve_config(self, supplied: Config | None) -> Config: ...

    def evaluate(self, data: QInput, config: Config) -> QResult: ...


class EventPlugin(Protocol):
    @property
    def descriptor(self) -> Descriptor: ...

    def resolve_config(self, supplied: Config | None) -> Config: ...

    def evaluate(self, data: QInput, structure: QResult, config: Config) -> QResult: ...

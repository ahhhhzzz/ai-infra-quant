"""Bounded independent research with evidence saved before final reasoning."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Protocol
from uuid import uuid4

from ai_infra_quant.application.paqs_e_models import ModelDescriptor
from ai_infra_quant.application.paqs_e_research import ExternalResearchFailure, WebResearch
from ai_infra_quant.core.domain.paqs_e_reasoning import AuxiliaryContextItem
from ai_infra_quant.core.domain.paqs_market_snapshot import PaqsMarketSnapshot, canonical_json


def uses_external_research(model: ModelDescriptor) -> bool:
    return model.enabled and model.provider_id == "deepseek" and not model.web_research_supported


class SearchEvidenceStore(Protocol):
    def record(
        self,
        research_id: str,
        snapshot: PaqsMarketSnapshot,
        status: str,
        payload: dict[str, object],
    ) -> None: ...


class SavedExternalResearch:
    def __init__(self, provider: WebResearch, store: SearchEvidenceStore) -> None:
        self.provider, self.store = provider, store

    def research(
        self, model: ModelDescriptor, snapshot: PaqsMarketSnapshot
    ) -> tuple[AuxiliaryContextItem, ...]:
        research_id = str(uuid4())
        try:
            context = self.provider.research(model, snapshot)
        except ExternalResearchFailure as error:
            self.store.record(
                research_id,
                snapshot,
                "FAILED",
                {
                    **error.evidence,
                    "provider": "tavily",
                    "research_id": research_id,
                    "failure_code": error.failure_code,
                },
            )
            error.research_id = research_id
            raise
        provenance = json.loads(context[0].provenance or "{}")
        provenance["research_id"] = research_id
        context = (replace(context[0], provenance=canonical_json(provenance)), *context[1:])
        self.store.record(
            research_id,
            snapshot,
            "SUCCEEDED",
            {
                "provider": "tavily",
                "research_id": research_id,
                "auxiliary_context": json.loads(canonical_json(context)),
            },
        )
        return context

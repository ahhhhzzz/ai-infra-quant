"""Current catalog capability, using synthetic transport only (no paid calls)."""

import pytest
from paqs_e_support import MemoryCredentials
from test_paqs_e_model_gateway import Transport, envelope
from test_paqs_e_narrative_provider import TEXT, request_for
from test_paqs_e_runtime import _snapshot

from ai_infra_quant.application.paqs_e_models import ModelCredentials, ModelRegistry
from ai_infra_quant.application.paqs_e_narrative import load_narrative_prompt
from ai_infra_quant.application.paqs_e_research import ResearchFailure
from ai_infra_quant.application.paqs_e_runtime import load_strategy_package
from ai_infra_quant.core.domain.paqs_e_narrative import NarrativeSuccess
from ai_infra_quant.integrations.openai_reasoning.gateway import ModelGateway
from ai_infra_quant.integrations.openai_reasoning.narrative import NarrativeGateway


def test_current_deepseek_rejects_research_without_transport_and_off_preserves_exact_text():
    registry = ModelRegistry()
    model = registry.resolve("deepseek-flash")
    store = MemoryCredentials()
    store.values["deepseek"] = "synthetic-shared-credential"
    credentials = ModelCredentials(registry, store)
    transport = Transport(envelope(TEXT, "responses", "deepseek-flash"))
    for key in ("deepseek-flash", "deepseek-v4-pro"):
        with pytest.raises(ResearchFailure):
            ModelGateway(registry, credentials, transport).research(
                registry.resolve(key), _snapshot()
            )
    assert transport.calls == []
    with pytest.raises(ValueError):
        registry.resolve("deepseek-v4-flash")  # retired selection, old records remain readable
    result = NarrativeGateway(registry, credentials, transport).reason_text(
        request=request_for(model), strategy=load_strategy_package(), prompt=load_narrative_prompt()
    )
    assert result == NarrativeSuccess(TEXT, "synthetic-response")
    assert len(transport.calls) == 1
    assert transport.calls[0][2]["model"] == "deepseek-flash"
    assert transport.calls[0][2]["tools"] == []

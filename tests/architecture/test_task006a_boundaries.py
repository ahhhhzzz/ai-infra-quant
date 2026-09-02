from __future__ import annotations

from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_paqs_input_core_is_provider_agnostic_and_decimal_only() -> None:
    source = _source("src/ai_infra_quant/core/domain/paqs_input.py")
    assert "integrations" not in source
    assert "ai_infra_quant.integrations" not in source
    assert "futu_quote" not in source
    assert "DataFrame" not in source
    assert "OpenQuoteContext" not in source
    assert "float(" not in source
    assert "Decimal" in source


def test_task006a_introduces_no_account_or_write_provider_capability() -> None:
    sources = "\n".join(
        _source(path)
        for path in (
            "src/ai_infra_quant/core/ports/market_data.py",
            "src/ai_infra_quant/integrations/futu_quote/adapter.py",
            "src/ai_infra_quant/application/supported_security_service.py",
            "src/ai_infra_quant/application/paqs_input_queries.py",
        )
    ).lower()
    for forbidden in (
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
        "trade_password",
        "broker_account",
    ):
        assert forbidden not in sources


def test_phase_one_migration_set_remains_exactly_one_revision() -> None:
    revisions = sorted(
        path.name for path in Path("src/ai_infra_quant/database/migrations/versions").glob("*.py")
    )
    assert revisions == ["0001_phase1_foundation.py"]

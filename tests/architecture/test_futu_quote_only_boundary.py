from pathlib import Path

INTEGRATION_ROOT = (
    Path(__file__).parents[2] / "src" / "ai_infra_quant" / "integrations" / "futu_quote"
)


def test_futu_integration_contains_no_trade_context_or_write_capability() -> None:
    forbidden = (
        "OpenSecTradeContext",
        "OpenFutureTradeContext",
        "place_order",
        "cancel_order",
        "modify_order",
        "unlock_trade",
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(INTEGRATION_ROOT.glob("*.py"))
    )
    assert all(symbol not in source for symbol in forbidden)

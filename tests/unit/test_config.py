from decimal import Decimal

import pytest
from pydantic import ValidationError

from ai_infra_quant.config import Settings
from ai_infra_quant.logging_config import redact


def test_safe_defaults() -> None:
    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.auto_execution is False
    assert settings.active_broker == "paper"
    assert settings.market_data_provider == "none"
    assert settings.futu_opend_host == "127.0.0.1"
    assert settings.futu_opend_port == 11111


def test_futu_market_data_provider_is_allowed_without_changing_safe_default() -> None:
    assert Settings(market_data_provider="futu").market_data_provider == "futu"


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"auto_execution": True}, "AUTO_EXECUTION"),
        ({"host": "0.0.0.0"}, "loopback"),
        ({"api_base_url": "http://example.com"}, "loopback"),
        ({"active_broker": "futu"}, "paper"),
        ({"market_data_provider": "other"}, "none or futu"),
        ({"initial_base_currency": "HK"}, "three uppercase"),
        ({"initial_portfolio_name": "   "}, "portfolio name"),
        ({"valuation_timezone": "Not/A_Timezone"}, "IANA timezone"),
        ({"futu_opend_host": "192.0.2.1"}, "loopback"),
        ({"futu_opend_port": 0}, "between 1 and 65535"),
        ({"trading_mode": "LIVE"}, "PAPER"),
    ],
)
def test_unsafe_configuration_is_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings.model_validate(override)


def test_initial_economics_must_balance() -> None:
    with pytest.raises(ValidationError, match="capital divided by units"):
        Settings.model_validate(
            {"initial_capital": "20000", "initial_units": "100", "initial_nav": "100"}
        )


def test_decimal_settings_reject_float_and_logging_redacts_sensitive_keys() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"initial_capital": Decimal("20000"), "initial_units": 200.0})
    assert redact(
        {"api_token": "not-a-real-secret", "nested": {"external_account_id": "private"}}
    ) == {"api_token": "[REDACTED]", "nested": {"external_account_id": "[REDACTED]"}}

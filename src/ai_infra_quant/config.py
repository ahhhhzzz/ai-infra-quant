from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from ipaddress import ip_address
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(StrEnum):
    PAPER = "PAPER"


def _decimal_setting(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool | float):
        raise ValueError(f"{field_name} must be an exact decimal string")
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a finite decimal") from exc
    if not decimal_value.is_finite() or decimal_value <= 0:
        raise ValueError(f"{field_name} must be positive and finite")
    return decimal_value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    app_env: str = "development"
    database_url: str = "sqlite:///./data/ai_infra_quant.db"
    host: str = "127.0.0.1"
    port: int = 8000
    trading_mode: TradingMode = TradingMode.PAPER
    auto_execution: bool = False
    active_broker: str = "paper"
    market_data_provider: str = "none"
    fundamental_data_provider: str = "none"
    event_data_provider: str = "none"
    api_base_url: str = "http://127.0.0.1:8000"
    initial_portfolio_name: str = "AI Infra"
    initial_base_currency: str = "HKD"
    initial_capital: Decimal = Decimal("20000")
    initial_units: Decimal = Decimal("200")
    initial_nav: Decimal = Decimal("100")
    inception_date: date = date(2026, 8, 31)
    valuation_timezone: str = "Asia/Hong_Kong"
    futu_opend_host: str = "127.0.0.1"
    futu_opend_port: int = 11111
    openai_api_key: SecretStr | None = None

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def normalize_optional_openai_api_key(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("host")
    @classmethod
    def validate_loopback_host(cls, value: str) -> str:
        try:
            if not ip_address(value).is_loopback:
                raise ValueError("Phase 1 must bind to a loopback address")
        except ValueError as exc:
            if "loopback" in str(exc):
                raise
            raise ValueError("Phase 1 host must be a literal loopback IP address") from exc
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return value

    @field_validator("futu_opend_host")
    @classmethod
    def validate_futu_opend_host(cls, value: str) -> str:
        try:
            if not ip_address(value).is_loopback:
                raise ValueError("FUTU_OPEND_HOST must be a loopback address")
        except ValueError as exc:
            if "loopback" in str(exc):
                raise
            raise ValueError("FUTU_OPEND_HOST must be a literal loopback IP address") from exc
        return value

    @field_validator("futu_opend_port")
    @classmethod
    def validate_futu_opend_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("FUTU_OPEND_PORT must be between 1 and 65535")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith("sqlite:///"):
            raise ValueError("Phase 1 runtime supports SQLite only")
        return value

    @field_validator("active_broker")
    @classmethod
    def validate_broker(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != "paper":
            raise ValueError("Phase 1 active broker descriptor must be paper")
        return normalized

    @field_validator("market_data_provider")
    @classmethod
    def validate_market_data_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"none", "futu"}:
            raise ValueError("MARKET_DATA_PROVIDER must be none or futu")
        return normalized

    @field_validator("fundamental_data_provider", "event_data_provider")
    @classmethod
    def validate_unimplemented_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != "none":
            raise ValueError("Phase 1 providers must be none")
        return normalized

    @field_validator("initial_base_currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
            raise ValueError("currency must be three uppercase ASCII letters")
        return normalized

    @field_validator("initial_portfolio_name")
    @classmethod
    def validate_portfolio_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 120:
            raise ValueError("initial portfolio name must contain 1-120 characters")
        return normalized

    @field_validator("valuation_timezone")
    @classmethod
    def validate_valuation_timezone(cls, value: str) -> str:
        normalized = value.strip()
        try:
            return ZoneInfo(normalized).key
        except ZoneInfoNotFoundError as exc:
            raise ValueError("valuation timezone must be a valid IANA timezone") from exc

    @field_validator("initial_capital", "initial_units", "initial_nav", mode="before")
    @classmethod
    def validate_initial_decimal(cls, value: object, info: object) -> Decimal:
        field_name = getattr(info, "field_name", "initial value")
        return _decimal_setting(value, field_name)

    @model_validator(mode="after")
    def enforce_phase_one_safety(self) -> Settings:
        if self.auto_execution:
            raise ValueError("AUTO_EXECUTION must be false in Phase 1")
        parsed = urlparse(self.api_base_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
            raise ValueError("API_BASE_URL must be an absolute HTTP URL")
        try:
            if not ip_address(parsed.hostname).is_loopback:
                raise ValueError("API_BASE_URL must use a loopback host in Phase 1")
        except ValueError as exc:
            if "loopback" in str(exc):
                raise
            raise ValueError("API_BASE_URL must use a literal loopback IP address") from exc
        if self.initial_capital / self.initial_units != self.initial_nav:
            raise ValueError("initial capital divided by units must equal initial NAV")
        return self

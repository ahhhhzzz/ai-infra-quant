from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TypeDecorator, TypeEngine

from ai_infra_quant.core.domain.common import require_utc
from ai_infra_quant.core.domain.money import parse_decimal

_CANONICAL_STORAGE = re.compile(r"^-?[0-9]{20}\.[0-9]{18}$")
_CANONICAL_UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$")


class ExactDecimal(TypeDecorator[Decimal]):
    """Dialect-exact Decimal: SQLite canonical TEXT, PostgreSQL NUMERIC."""

    impl = String
    cache_ok = True

    def __init__(self, precision: int = 38, scale: int = 18) -> None:
        if (precision, scale) != (38, 18):
            raise ValueError("Phase 1 ExactDecimal must be ExactDecimal(38, 18)")
        self.precision = precision
        self.scale = scale
        super().__init__(length=40)

    def load_dialect_impl(self, dialect: Any) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return cast(
                TypeEngine[Any],
                dialect.type_descriptor(Numeric(self.precision, self.scale, asdecimal=True)),
            )
        return cast(TypeEngine[Any], dialect.type_descriptor(String(40)))

    @staticmethod
    def canonical_storage(value: Decimal | str) -> str:
        parsed = parse_decimal(value)
        if parsed == 0:
            parsed = parsed.copy_abs()
        rendered = format(parsed, "f")
        sign = ""
        if rendered.startswith("-"):
            sign, rendered = "-", rendered[1:]
        integer, separator, fraction = rendered.partition(".")
        if not separator:
            fraction = ""
        if len(integer) > 20 or len(fraction) > 18:
            raise ValueError("financial value exceeds ExactDecimal(38,18)")
        stored = f"{sign}{integer.zfill(20)}.{fraction.ljust(18, '0')}"
        if not _CANONICAL_STORAGE.fullmatch(stored):
            raise ValueError("could not produce canonical decimal storage")
        return stored

    def process_bind_param(self, value: object, dialect: Any) -> Decimal | str | None:
        if value is None:
            return None
        if not isinstance(value, Decimal | str):
            raise TypeError("ExactDecimal rejects floats and non-decimal numeric types")
        parsed = parse_decimal(value)
        if dialect.name == "postgresql":
            return parsed
        return self.canonical_storage(parsed)

    def process_result_value(self, value: object, dialect: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, float | bool):
            raise TypeError("database returned a non-exact financial value")
        if isinstance(value, Decimal):
            return parse_decimal(value)
        if not isinstance(value, str):
            raise TypeError("database returned an unsupported financial value")
        if dialect.name == "sqlite":
            if not _CANONICAL_STORAGE.fullmatch(value):
                raise ValueError("SQLite returned non-canonical decimal TEXT")
            return parse_decimal(Decimal(value))
        return parse_decimal(value)


@compiles(ExactDecimal, "sqlite")
def compile_exact_decimal_sqlite(type_: ExactDecimal, compiler: Any, **kw: Any) -> str:
    del type_, compiler, kw
    return "TEXT"


@compiles(ExactDecimal, "postgresql")
def compile_exact_decimal_postgresql(type_: ExactDecimal, compiler: Any, **kw: Any) -> str:
    del compiler, kw
    return f"NUMERIC({type_.precision},{type_.scale})"


class UTCDateTime(TypeDecorator[datetime]):
    """Store an exact UTC instant as SQLite TEXT or PostgreSQL timestamptz."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return cast(TypeEngine[Any], dialect.type_descriptor(String(27)))
        return cast(TypeEngine[Any], dialect.type_descriptor(DateTime(timezone=True)))

    def process_bind_param(self, value: object, dialect: Any) -> datetime | str | None:
        if value is None:
            return None
        if not isinstance(value, datetime):
            raise TypeError("UTCDateTime accepts datetime values only")
        normalized = require_utc(value)
        if dialect.name == "sqlite":
            return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")
        return normalized

    def process_result_value(self, value: object, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            if dialect.name != "sqlite" or _CANONICAL_UTC.fullmatch(value) is None:
                raise ValueError("database returned a non-canonical UTC datetime")
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        if not isinstance(value, datetime):
            raise TypeError("database returned an unsupported datetime value")
        return require_utc(value)


@compiles(UTCDateTime, "sqlite")
def compile_utc_datetime_sqlite(type_: UTCDateTime, compiler: Any, **kw: Any) -> str:
    del type_, compiler, kw
    return "TEXT"


@compiles(UTCDateTime, "postgresql")
def compile_utc_datetime_postgresql(type_: UTCDateTime, compiler: Any, **kw: Any) -> str:
    del type_, compiler, kw
    return "TIMESTAMP WITH TIME ZONE"

"""Normative paqs-q-canonical-v1 encoding and tagged SHA-256 preimages."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


def decimal_text(value: Decimal) -> str:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("FINITE_DECIMAL_REQUIRED")
    if value.is_zero():
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("AWARE_DATETIME_REQUIRED")
    return value.astimezone(UTC)


def primitive(value: Any) -> Any:
    if isinstance(value, Decimal):
        return decimal_text(value)
    if isinstance(value, datetime):
        return utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ValueError("UNPAIRED_SURROGATE")
        return value
    if value is None or type(value) in (bool, int):
        return value
    if isinstance(value, Mapping):
        if any(type(k) is not str or not k.isascii() for k in value):
            raise ValueError("ASCII_SCHEMA_KEYS_REQUIRED")
        return {k: primitive(v) for k, v in value.items()}
    if isinstance(value, tuple | list):
        return [primitive(v) for v in value]
    raise ValueError("NONCANONICAL_TYPE")


def canonical(value: Any) -> bytes:
    return json.dumps(
        primitive(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    if not tag.isascii() or "\0" in tag or not tag:
        raise ValueError("INVALID_HASH_DOMAIN")
    return sha256(tag.encode("ascii") + b"\0" + canonical(value)).hexdigest()


def hash_text(value: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("INVALID_SHA256")
    return value


def legacy_digest(tag: str, value: Any) -> str:
    """Pinned R04 lineage only. Never used for new framework identities."""
    text = json.dumps(primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256((tag + "\0" + text).encode("utf-8")).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class FrozenJSON:
    """Immutable canonical value. document() returns a detached mutable copy."""

    data: bytes

    def __post_init__(self) -> None:
        if type(self.data) is not bytes:
            raise ValueError("IMMUTABLE_BYTES_REQUIRED")
        value = json.loads(self.data, object_pairs_hook=_pairs)
        if canonical(value) != self.data:
            raise ValueError("NONCANONICAL_JSON_BYTES")

    @classmethod
    def of(cls, value: Any) -> "FrozenJSON":
        return cls(canonical(value))

    def document(self) -> Any:
        return json.loads(self.data)

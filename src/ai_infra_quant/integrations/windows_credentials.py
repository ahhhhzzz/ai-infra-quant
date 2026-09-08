"""Windows user Credential Manager. No file, database or keyring fallback."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import Any, ClassVar

from ai_infra_quant.core.ports.credentials import CredentialStoreUnavailable


class _Credential(ctypes.Structure):
    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialStore:
    def __init__(self, slots: frozenset[str]) -> None:
        self._slots = slots

    def _target(self, slot: str) -> str:
        if slot not in self._slots:
            raise ValueError("Unregistered credential slot")
        return "ai-infra-quant/paqs-e/" + slot

    @staticmethod
    def _api() -> Any:
        if sys.platform != "win32":
            raise CredentialStoreUnavailable()
        try:
            api = ctypes.WinDLL("advapi32", use_last_error=True)
            pointer = ctypes.POINTER(_Credential)
            api.CredReadW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(pointer),
            ]
            api.CredReadW.restype = wintypes.BOOL
            api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
            api.CredWriteW.restype = wintypes.BOOL
            api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
            api.CredDeleteW.restype = wintypes.BOOL
            api.CredFree.argtypes = [ctypes.c_void_p]
            api.CredFree.restype = None
            return api
        except Exception:
            raise CredentialStoreUnavailable() from None

    def read(self, slot: str) -> str | None:
        target = self._target(slot)
        api = self._api()
        pointer = ctypes.POINTER(_Credential)()
        if not api.CredReadW(target, 1, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168:
                return None
            raise CredentialStoreUnavailable()
        try:
            value = pointer.contents
            if not 0 < value.CredentialBlobSize <= 2048:
                raise CredentialStoreUnavailable()
            return ctypes.string_at(value.CredentialBlob, value.CredentialBlobSize).decode("utf-8")
        except (ValueError, UnicodeError):
            raise CredentialStoreUnavailable() from None
        finally:
            api.CredFree(pointer)

    def save(self, slot: str, secret: str) -> None:
        target = self._target(slot)
        api = self._api()
        encoded = secret.encode("utf-8")
        if not 0 < len(encoded) <= 2048:
            raise ValueError("Invalid credential length")
        buffer = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
        credential = _Credential()
        credential.Type = 1  # CRED_TYPE_GENERIC, isolated target namespace.
        credential.TargetName = target
        credential.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE, current user's credential set.
        credential.CredentialBlobSize = len(encoded)
        credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        try:
            if not api.CredWriteW(ctypes.byref(credential), 0):
                raise CredentialStoreUnavailable()
        finally:
            ctypes.memset(buffer, 0, len(encoded))

    def delete(self, slot: str) -> None:
        target = self._target(slot)
        api = self._api()
        if not api.CredDeleteW(target, 1, 0) and ctypes.get_last_error() != 1168:
            raise CredentialStoreUnavailable()

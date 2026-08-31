from __future__ import annotations

from collections.abc import Callable

from ai_infra_quant.core.ports.repositories import UnitOfWork

UnitOfWorkFactory = Callable[[], UnitOfWork]

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]

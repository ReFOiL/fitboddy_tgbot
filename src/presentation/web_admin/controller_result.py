from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import HTTPException

T = TypeVar("T")


@dataclass(slots=True)
class ControllerResult(Generic[T]):
    ok: bool
    data: T | None = None
    error: str | None = None
    status_code: int = 200

    def unwrap(self) -> T:
        if not self.ok:
            raise HTTPException(status_code=self.status_code, detail=self.error or "Error")
        return self.data  # type: ignore[return-value]

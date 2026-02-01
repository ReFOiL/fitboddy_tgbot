from __future__ import annotations

from typing import TypeVar

from fastapi import status

from src.presentation.web_admin.controller_result import ControllerResult

T = TypeVar("T")


class BaseController:
    def ok(self, data: T) -> ControllerResult[T]:
        return ControllerResult(ok=True, data=data, status_code=status.HTTP_200_OK)

    def not_found(self, detail: str = "Not found") -> ControllerResult[None]:
        return ControllerResult(
            ok=False,
            error=detail,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def bad_request(self, detail: str) -> ControllerResult[None]:
        return ControllerResult(
            ok=False,
            error=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

from __future__ import annotations

import structlog

from src.application.services.admin_users import AdminUserService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.user_presenters import UserPresenter
from src.presentation.web_admin.user_schemas import UserDetailOut, UserOut

logger = structlog.get_logger()


class UserController(BaseController):
    def __init__(self, service: AdminUserService, presenter: UserPresenter) -> None:
        super().__init__()
        self._service = service
        self._presenter = presenter

    async def list_all(self) -> ControllerResult[list[UserOut]]:
        users = await self._service.list_users()
        return self.ok([self._presenter.to_out(u) for u in users])

    async def get_detail(self, user_id: int) -> ControllerResult[UserDetailOut]:
        user = await self._service.get_user(user_id)
        if user is None:
            logger.warning("admin.user.detail_not_found", user_id=user_id)
            return ControllerResult(ok=False, error="User not found", status_code=404)
        answers = await self._service.list_user_answers(user_id)
        logger.info(
            "admin.user.detail_viewed",
            user_id=user_id,
            telegram_id=user.telegram_id,
            answers_count=len(answers),
        )
        return self.ok(self._presenter.to_detail_out(user, answers))


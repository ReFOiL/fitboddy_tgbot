from __future__ import annotations

import structlog

from src.application.services.custom_question_admin import CustomQuestionAdminService
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.question_presenters import QuestionPayloadBuilder, QuestionPresenter
from src.presentation.web_admin.question_schemas import (
    CustomQuestionCreate,
    CustomQuestionOut,
    CustomQuestionUpdate,
    MessageOut,
    QuestionCreatedOut,
)

logger = structlog.get_logger()


class QuestionController(BaseController):
    def __init__(
        self,
        service: CustomQuestionAdminService,
        builder: QuestionPayloadBuilder,
        presenter: QuestionPresenter,
    ) -> None:
        super().__init__()
        self._service = service
        self._builder = builder
        self._presenter = presenter

    async def create(self, data: CustomQuestionCreate) -> ControllerResult[QuestionCreatedOut]:
        payload_result = self._builder.build_create(data)
        if not payload_result.ok:
            return ControllerResult(
                ok=False,
                error=payload_result.error,
                status_code=payload_result.status_code,
            )
        question = await self._service.create(payload_result.data or {})
        logger.info(
            "admin.question.created",
            question_id=question.id,
            key=question.key,
            answer_type=str(question.answer_type),
        )
        return self.ok(QuestionCreatedOut(id=question.id, message="Question created"))

    async def list_all(self) -> ControllerResult[list[CustomQuestionOut]]:
        questions = await self._service.list_all()
        return self.ok([self._presenter.to_out(question) for question in questions])

    async def update(self, question_id: int, data: CustomQuestionUpdate) -> ControllerResult[MessageOut]:
        updates_result = self._builder.build_update(data)
        if not updates_result.ok:
            return ControllerResult(
                ok=False,
                error=updates_result.error,
                status_code=updates_result.status_code,
            )
        try:
            await self._service.update(question_id, updates_result.data or {})
            logger.info(
                "admin.question.updated",
                question_id=question_id,
                updated_fields=list((updates_result.data or {}).keys()),
            )
        except ValueError:
            logger.warning("admin.question.update_not_found", question_id=question_id)
            return self.not_found("Question not found")
        return self.ok(MessageOut(message="Question updated"))

    async def deactivate(self, question_id: int) -> ControllerResult[MessageOut]:
        try:
            await self._service.deactivate(question_id)
            logger.info("admin.question.deactivated", question_id=question_id)
        except ValueError:
            logger.warning("admin.question.deactivate_not_found", question_id=question_id)
            return self.not_found("Question not found")
        return self.ok(MessageOut(message="Question deactivated"))

    async def update_order(self, question_id: int, data: object) -> ControllerResult[MessageOut]:
        try:
            await self._service.update_order(question_id, data.new_order)  # type: ignore[attr-defined]
        except ValueError:
            return self.not_found("Question not found")
        return self.ok(MessageOut(message="Order updated"))

    async def link_template(self, question_id: int, template_id: int) -> ControllerResult[MessageOut]:
        await self._service.link_template(question_id, template_id)
        logger.info("admin.question.template_linked", question_id=question_id, template_id=template_id)
        return self.ok(MessageOut(message="Link created"))

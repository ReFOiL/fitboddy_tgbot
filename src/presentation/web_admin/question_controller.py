from __future__ import annotations

import structlog

from src.application.services.custom_question_admin import CustomQuestionAdminService
from src.commons.exceptions import SystemQuestionMutationError
from src.presentation.web_admin.controller_base import BaseController
from src.presentation.web_admin.controller_result import ControllerResult
from src.presentation.web_admin.question_presenters import QuestionPayloadBuilder, QuestionPresenter
from src.presentation.web_admin.question_schemas import (
    CustomQuestionCreate,
    CustomQuestionOut,
    CustomQuestionUpdate,
    MessageOut,
    QuestionCreatedOut,
    QuestionOrderUpdate,
    ScoringWeightCreate,
    ScoringWeightOut,
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
        try:
            question = await self._service.create(payload_result.data or {})
        except SystemQuestionMutationError as exc:
            logger.warning("admin.question.create_forbidden", error=exc.message)
            return self.bad_request(exc.message)
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
        except SystemQuestionMutationError as exc:
            logger.warning("admin.question.update_forbidden", question_id=question_id, error=exc.message)
            return self.bad_request(exc.message)
        except ValueError:
            logger.warning("admin.question.update_not_found", question_id=question_id)
            return self.not_found("Question not found")
        return self.ok(MessageOut(message="Question updated"))

    async def deactivate(self, question_id: int) -> ControllerResult[MessageOut]:
        try:
            await self._service.deactivate(question_id)
            logger.info("admin.question.deactivated", question_id=question_id)
        except SystemQuestionMutationError as exc:
            logger.warning("admin.question.deactivate_forbidden", question_id=question_id, error=exc.message)
            return self.bad_request(exc.message)
        except ValueError:
            logger.warning("admin.question.deactivate_not_found", question_id=question_id)
            return self.not_found("Question not found")
        return self.ok(MessageOut(message="Question deactivated"))

    async def update_order(self, question_id: int, data: QuestionOrderUpdate) -> ControllerResult[MessageOut]:
        try:
            await self._service.update_order(question_id, data.new_order)
        except ValueError:
            return self.not_found("Question not found")
        return self.ok(MessageOut(message="Order updated"))

    async def list_scoring_weights(self, question_id: int) -> ControllerResult[list[ScoringWeightOut]]:
        try:
            weights = await self._service.list_scoring_weights(question_id)
            return self.ok([ScoringWeightOut.model_validate(w) for w in weights])
        except ValueError:
            return self.not_found("Question not found")

    async def create_or_update_scoring_weight(
        self, question_id: int, data: ScoringWeightCreate
    ) -> ControllerResult[ScoringWeightOut]:
        try:
            weight = await self._service.create_or_update_scoring_weight(
                question_id, data.answer_value, data.weight
            )
            logger.info(
                "admin.question.scoring_weight_updated",
                question_id=question_id,
                answer_value=data.answer_value,
                weight=data.weight,
            )
            return self.ok(ScoringWeightOut.model_validate(weight))
        except ValueError as e:
            logger.warning("admin.question.scoring_weight_failed", question_id=question_id, error=str(e))
            return self.not_found(str(e))

    async def delete_scoring_weight(
        self, question_id: int, answer_value: str
    ) -> ControllerResult[MessageOut]:
        try:
            await self._service.delete_scoring_weight(question_id, answer_value)
            logger.info(
                "admin.question.scoring_weight_deleted",
                question_id=question_id,
                answer_value=answer_value,
            )
            return self.ok(MessageOut(message="Scoring weight deleted"))
        except ValueError as e:
            logger.warning("admin.question.scoring_weight_delete_failed", question_id=question_id, error=str(e))
            return self.not_found(str(e))

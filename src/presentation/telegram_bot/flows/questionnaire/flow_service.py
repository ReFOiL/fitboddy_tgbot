from __future__ import annotations

import structlog

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.application.services.questionnaire_flow_queries import QuestionnaireFlowQueries
from src.application.services.questionnaire_answers import QuestionnaireAnswerService
from src.application.services.profile_completion import ProfileCompletionService
from src.application.services.user_plan_service import UserPlanService
from src.application.services.user_registration import UserRegistrationService
from src.domain.questionnaire import Question
from src.presentation.telegram_bot.flows import (
    BaseFlow,
    EnsureUserMixin,
    NavigationMixin,
    UserContextMixin,
)
from src.presentation.telegram_bot.flows.questionnaire.presenter import QuestionnairePresenter
from src.presentation.telegram_bot.flows.questionnaire.state_service import QuestionnaireStateService
from src.presentation.telegram_bot.flows.questionnaire.navigation import QuestionNavigation
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts

logger = structlog.get_logger()


class QuestionnaireFlow(BaseFlow, UserContextMixin, EnsureUserMixin, NavigationMixin):
    def __init__(
        self,
        queries: QuestionnaireFlowQueries,
        user_service: UserRegistrationService,
        profile_service: ProfileCompletionService,
        answer_service: QuestionnaireAnswerService,
        presenter: QuestionnairePresenter | None = None,
        user_plan_service: UserPlanService | None = None,
    ) -> None:
        self._queries = queries
        self._user_service = user_service
        self._profile_service = profile_service
        self._answer_service = answer_service
        self._presenter = presenter or QuestionnairePresenter()
        self._user_plan_service = user_plan_service

    async def start(self, message: Message, state: FSMContext) -> None:
        state_service = QuestionnaireStateService(state)
        db_user_id = await self._ensure_db_user_id(message, state_service)
        if db_user_id is None:
            return
        await self._next_or_finish(message, state_service)

    async def process(self, message: Message, state: FSMContext) -> None:
        text = message.text or ""
        if self._is_exit(text):
            await QuestionnaireStateService(state).clear()
            await message.answer(BotTexts.QUESTIONNAIRE_FINISHED_PROMPT, reply_markup=main_menu())
            return

        state_service = QuestionnaireStateService(state)
        db_user_id = await self._ensure_db_user_id(message, state_service)
        if db_user_id is None:
            return
        current_key = await state_service.get_current_key()
        if not current_key:
            await self._next_or_finish(message, state_service)
            return

        question = await self._queries.question_by_key(current_key)
        if question is None:
            await state_service.clear()
            await message.answer(BotTexts.QUESTIONNAIRE_UPDATED_RESTART, reply_markup=main_menu())
            return

        if self._is_back(text):
            await self._handle_back(message, state_service, question)
            return

        value, error = self._answer_service.validate(question, text)
        if error:
            await message.answer(error)
            return
        saved = await self._answer_service.save(db_user_id, question, value)
        if not saved:
            await message.answer(BotTexts.QUESTIONNAIRE_SAVE_ERROR)
            return
        await self._next_or_finish(message, state_service)

    async def _next_or_finish(self, message: Message, state_service: QuestionnaireStateService) -> None:
        db_user_id = await state_service.get_user_db_id()
        if db_user_id is None:
            # Fallback: try to resolve again (state может быть очищен/потерян)
            db_user_id = await self._ensure_db_user_id(message, state_service)
        if db_user_id is None:
            return
        question, is_completed = await self._queries.next_question(db_user_id)
        if is_completed:
            await self._profile_service.mark_completed(db_user_id)
            if self._user_plan_service is not None:
                try:
                    plan = await self._user_plan_service.get_or_create_plan(db_user_id)
                    logger.info(
                        "questionnaire.plan_after_completion",
                        user_id=db_user_id,
                        plan_created=plan is not None,
                    )
                except Exception:
                    logger.exception("questionnaire.plan_after_completion_failed", user_id=db_user_id)
            await state_service.clear()
            await message.answer(BotTexts.QUESTIONNAIRE_COMPLETED, reply_markup=main_menu())
            return
        if question is None:
            await message.answer(BotTexts.QUESTIONNAIRE_LOAD_ERROR, reply_markup=main_menu())
            return
        navigation = QuestionNavigation(self._queries, state_service)
        include_back = await navigation.has_prev(question.key)
        await state_service.set_current_key(question.key)
        await self._send_question(message, question, include_back)

    async def _handle_back(self, message: Message, state_service: QuestionnaireStateService, question: Question) -> None:
        navigation = QuestionNavigation(self._queries, state_service)
        prev_key = await navigation.prev_key(question.key)
        if prev_key is None:
            await self._send_question(message, question, False)
            return
        prev_question = await self._queries.question_by_key(prev_key)
        if prev_question is None:
            await self._send_question(message, question, False)
            return
        await state_service.set_current_key(prev_key)
        include_back = await navigation.has_prev(prev_key)
        await self._send_question(
            message,
            prev_question,
            include_back,
        )

    async def _send_question(self, message: Message, question: Question, include_back: bool) -> None:
        render = self._presenter.render_question(question, include_back)
        await message.answer(render.text, reply_markup=render.keyboard)

    async def _ensure_db_user_id(
        self,
        message: Message,
        state_service: QuestionnaireStateService,
    ) -> int | None:
        cached = await state_service.get_user_db_id()
        if cached is not None:
            return cached
        user = await self._ensure_user(message, self._user_service)
        if user is None or user.id is None:
            return None
        await state_service.set_user_db_id(user.id)
        return user.id



from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.metrics import workouts_generated_total
from src.application.use_cases.workout_generator.simple_matcher import SimpleWorkoutMatcher
from src.presentation.telegram_bot.flows import BaseFlow, NavigationMixin, ResetStateMixin, UserContextMixin
from src.presentation.telegram_bot.flows.workouts.presenter import WorkoutPlanPresenter
from src.presentation.telegram_bot.keyboards.builders import main_menu
from src.presentation.telegram_bot.texts import BotTexts
from src.presentation.telegram_bot.flows.workouts.link_map_builder import LinkMapBuilder


class WorkoutsFlow(BaseFlow, UserContextMixin, NavigationMixin, ResetStateMixin):
    def __init__(
        self,
        uow: UnitOfWork,
        matcher: SimpleWorkoutMatcher,
        presenter: WorkoutPlanPresenter | None = None,
        link_map_builder: LinkMapBuilder | None = None,
    ) -> None:
        self._uow = uow
        self._matcher = matcher
        self._presenter = presenter or WorkoutPlanPresenter()
        self._link_map_builder = link_map_builder or LinkMapBuilder()

    async def start(self, message: Message, state: FSMContext) -> None:
        await self._reset_state(state)
        await self.process(message, state)

    async def process(self, message: Message, state: FSMContext) -> None:
        user_id = self._user_id(message)
        if user_id is None:
            return
        text = message.text or ""
        if self._is_exit(text):
            await message.answer(BotTexts.WORKOUTS_EXITED, reply_markup=main_menu())
            return
        async with self._uow:
            user = await self._uow.users.get_by_telegram_id(user_id)
            if user is None:
                await message.answer(BotTexts.WORKOUTS_REGISTER_FIRST, reply_markup=main_menu())
                return
            answers = await self._uow.user_answers.list_by_user_id(user.id)
            if not answers:
                await message.answer(BotTexts.WORKOUTS_COMPLETE_QUESTIONNAIRE, reply_markup=main_menu())
                return
            templates = await self._uow.workouts.list_all()
            links = await self._uow.question_template_links.list_all()

        if not templates:
            await message.answer(BotTexts.WORKOUTS_NO_TEMPLATES, reply_markup=main_menu())
            return

        link_map = self._link_map_builder.build(links)
        matched = await self._matcher.match(answers, templates, link_map or None)
        if not matched:
            await message.answer(BotTexts.WORKOUTS_NO_MATCH, reply_markup=main_menu())
            return

        workouts_generated_total.inc()
        await message.answer(self._presenter.format_plan(matched), reply_markup=main_menu())


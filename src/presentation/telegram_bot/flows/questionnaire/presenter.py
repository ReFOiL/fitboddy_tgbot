from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import ReplyKeyboardMarkup

from src.domain.questionnaire import Question
from src.domain.value_objects.questionnaire import AnswerType
from src.presentation.telegram_bot.flows.navigation_mixin import NavigationMixin
from src.presentation.telegram_bot.keyboards.builders import reply_keyboard
from src.presentation.telegram_bot.texts import BotTexts


@dataclass(slots=True)
class QuestionRender:
    text: str
    keyboard: ReplyKeyboardMarkup


class QuestionnairePresenter(NavigationMixin):
    MULTI_DONE_BUTTON = "✅ Готово"

    def render_question(
        self,
        question: Question,
        include_back: bool,
        selected_values: list[str] | None = None,
    ) -> QuestionRender:
        options = [option.label for option in question.options]
        if question.answer_type in {AnswerType.SINGLE_CHOICE, AnswerType.MULTIPLE_CHOICE, AnswerType.BOOLEAN}:
            if question.answer_type == AnswerType.MULTIPLE_CHOICE:
                return self._render_multiple_choice(question, include_back, selected_values or [])
            if question.answer_type == AnswerType.BOOLEAN and not options:
                options = [BotTexts.QUESTIONNAIRE_YES, BotTexts.QUESTIONNAIRE_NO]
            keyboard = reply_keyboard(self._with_nav(options, include_back, True), row_width=2)
            return QuestionRender(text=question.text, keyboard=keyboard)
        keyboard = reply_keyboard(self._with_nav([], include_back, True), row_width=2)
        return QuestionRender(text=question.text, keyboard=keyboard)

    def _render_multiple_choice(
        self,
        question: Question,
        include_back: bool,
        selected_values: list[str],
    ) -> QuestionRender:
        selected_set = set(selected_values)
        options = [
            f"{'☑️' if option.value in selected_set else '⬜'} {option.label}"
            for option in question.options
        ]
        options.append(self.MULTI_DONE_BUTTON)
        selected_human = [opt.label for opt in question.options if opt.value in selected_set]
        selected_line = ", ".join(selected_human) if selected_human else "пока ничего"
        text = (
            f"{question.text}\n\n"
            "Можно выбрать несколько вариантов.\n"
            f"Сейчас выбрано: {selected_line}\n"
            "Когда закончите выбор — нажмите «✅ Готово»."
        )
        keyboard = reply_keyboard(self._with_nav(options, include_back, True), row_width=2)
        return QuestionRender(text=text, keyboard=keyboard)

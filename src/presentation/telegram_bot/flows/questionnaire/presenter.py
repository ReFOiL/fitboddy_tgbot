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
    def render_question(self, question: Question, include_back: bool) -> QuestionRender:
        options = [option.label for option in question.options]
        if question.answer_type in {AnswerType.SINGLE_CHOICE, AnswerType.MULTIPLE_CHOICE, AnswerType.BOOLEAN}:
            if question.answer_type == AnswerType.BOOLEAN and not options:
                options = [BotTexts.QUESTIONNAIRE_YES, BotTexts.QUESTIONNAIRE_NO]
            keyboard = reply_keyboard(self._with_nav(options, include_back, True), row_width=2)
            return QuestionRender(text=question.text, keyboard=keyboard)
        keyboard = reply_keyboard(self._with_nav([], include_back, True), row_width=2)
        return QuestionRender(text=question.text, keyboard=keyboard)

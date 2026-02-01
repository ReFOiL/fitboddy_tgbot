from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption
from src.domain.value_objects.questionnaire import AnswerType


@dataclass(slots=True)
class QuestionOption:
    value: str
    label: str


@dataclass(slots=True)
class Question:
    key: str
    text: str
    answer_type: AnswerType
    options: list[QuestionOption]
    min_value: int | None = None
    max_value: int | None = None
    pattern: str | None = None
    is_required: bool = False


class QuestionFactory:
    def from_entity(self, question: CustomQuestion) -> Question:
        return Question(
            key=question.key,
            text=question.text,
            answer_type=question.answer_type,
            options=self._parse_options(question.options or []),
            min_value=question.min_value,
            max_value=question.max_value,
            pattern=question.pattern,
            is_required=question.is_required,
        )

    def _parse_options(self, raw: list[CustomQuestionOption]) -> list[QuestionOption]:
        options: list[QuestionOption] = []
        for item in raw:
            value = str(item.value).strip()
            label = str(item.label).strip()
            if not value:
                continue
            options.append(QuestionOption(value=value, label=label))
        return options

from __future__ import annotations

from src.domain.questionnaire.models import QuestionOption


def build_choice_map(options: list[QuestionOption]) -> dict[str, str]:
    value_map: dict[str, str] = {}
    for option in options:
        value_key = option.value.strip().lower()
        label_key = option.label.strip().lower()
        if value_key:
            value_map[value_key] = option.value
        if label_key:
            value_map[label_key] = option.value
    return value_map

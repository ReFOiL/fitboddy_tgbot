from __future__ import annotations

from collections.abc import Sequence

from src.domain.entities.user_answer import UserAnswer
from src.application.services.value_casting import ValueCasterProtocol, LenientCaster


class AnswerLookupMixin:
    answers: Sequence[UserAnswer]
    _caster: ValueCasterProtocol

    def _answers_for_key(self, key: str) -> list[UserAnswer]:
        return [ans for ans in self.answers if ans.question and ans.question.key == key]

    def get_value(self, key: str) -> object | None:
        items = self._answers_for_key(key)
        if not items:
            return None
        item = items[0]
        if item.option is not None:
            return item.option.value
        return item.value

    def get_values(self, key: str) -> list[str]:
        items = self._answers_for_key(key)
        values: list[str] = []
        for item in items:
            if item.option is not None:
                values.append(item.option.value)
                continue
            value = item.value
            if isinstance(value, str):
                values.append(value)
        return values

    def get_str(self, key: str) -> str | None:
        return self._caster.to_str(self.get_value(key))

    def get_int(self, key: str) -> int | None:
        return self._caster.to_int(self.get_value(key))

    def get_float(self, key: str) -> float | None:
        return self._caster.to_float(self.get_value(key))

    def get_str_list(self, key: str) -> list[str]:
        return self.get_values(key)


class AnswerLookup(AnswerLookupMixin):
    def __init__(self, answers: Sequence[UserAnswer], caster: ValueCasterProtocol | None = None) -> None:
        self.answers = answers
        self._caster = caster or LenientCaster()

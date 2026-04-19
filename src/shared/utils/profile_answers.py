from __future__ import annotations

from collections.abc import Sequence

from src.domain.entities.user_answer import UserAnswer
from src.application.services.value_casting import ValueCasterProtocol, LenientCaster


class UserAnswerExtractor:
    """Базовый класс для извлечения данных из UserAnswer."""

    @staticmethod
    def extract_value(answer: UserAnswer) -> str | int | float | bool | None:
        """
        Извлечь значение из UserAnswer.
        
        Приоритет: option.value > value
        """
        if answer.option is not None:
            return answer.option.value
        return answer.value

    @staticmethod
    def extract_values(answers: list[UserAnswer]) -> list[str]:
        """
        Извлечь список значений из списка UserAnswer.
        Используется для MULTIPLE_CHOICE вопросов.
        """
        values: list[str] = []
        for answer in answers:
            if answer.option is not None:
                values.append(answer.option.value)
            elif answer.value is not None:
                values.append(str(answer.value))
        return values

    @staticmethod
    def find_by_question_key(
        answers: list[UserAnswer], question_key: str
    ) -> UserAnswer | None:
        """Найти ответ по ключу вопроса."""
        for answer in answers:
            if answer.question and answer.question.key == question_key:
                return answer
        return None

    @staticmethod
    def extract_equipment_names(answer: UserAnswer) -> list[str]:
        """
        Извлечь список имен оборудования из ответа на system:equipment.
        
        Поддерживает:
        - SINGLE_CHOICE (option.value)
        - MULTIPLE_CHOICE (список UserAnswer или список в value)
        """
        equipment_names: list[str] = []
        
        if answer.option is not None:
            # SINGLE_CHOICE через option
            equipment_names = [answer.option.value]
        elif answer.value is not None:
            # MULTIPLE_CHOICE или SINGLE_CHOICE через value
            if isinstance(answer.value, list):
                equipment_names = [str(v) for v in answer.value]
            else:
                equipment_names = [str(answer.value)]
        
        # «Нет оборудования» и «другое» не мапятся на справочник equipment
        return [name for name in equipment_names if name not in ("none", "other")]


class AnswerLookupMixin(UserAnswerExtractor):
    """Mixin для работы с ответами пользователя через lookup по ключам."""
    
    answers: Sequence[UserAnswer]
    _caster: ValueCasterProtocol

    def _answers_for_key(self, key: str) -> list[UserAnswer]:
        return [ans for ans in self.answers if ans.question and ans.question.key == key]

    def get_value(self, key: str) -> object | None:
        """Получить значение ответа по ключу вопроса (работает для всех вопросов из UserAnswer)."""
        items = self._answers_for_key(key)
        if not items:
            return None
        
        # Для MULTIPLE_CHOICE возвращаем список значений
        if len(items) > 1:
            values: list[str] = []
            for item in items:
                if item.option is not None:
                    values.append(item.option.value)
                elif item.value is not None:
                    values.append(str(item.value))
            return values if values else None
        
        # Для SINGLE_CHOICE или других типов возвращаем одно значение
        item = items[0]
        if item.option is not None:
            return item.option.value
        return item.value

    def get_values(self, key: str) -> list[str]:
        """Получить список значений ответа по ключу вопроса."""
        items = self._answers_for_key(key)
        values: list[str] = []
        for item in items:
            if item.option is not None:
                values.append(item.option.value)
                continue
            value = item.value
            if isinstance(value, str):
                values.append(value)
            elif value is not None:
                values.append(str(value))
        return values

    def get_str(self, key: str) -> str | None:
        value = self.get_value(key)
        if value is None:
            return None
        # Приводим к нужному типу для caster
        cast_value: str | int | float | bool | None = None
        if isinstance(value, (str, int, float, bool)):
            cast_value = value
        elif value is not None:
            cast_value = str(value)
        return self._caster.to_str(cast_value)

    def get_int(self, key: str) -> int | None:
        value = self.get_value(key)
        if value is None:
            return None
        # Приводим к нужному типу для caster
        cast_value: str | int | float | bool | None = None
        if isinstance(value, (str, int, float, bool)):
            cast_value = value
        elif value is not None:
            cast_value = str(value)
        return self._caster.to_int(cast_value)

    def get_float(self, key: str) -> float | None:
        value = self.get_value(key)
        if value is None:
            return None
        # Приводим к нужному типу для caster
        cast_value: str | int | float | bool | None = None
        if isinstance(value, (str, int, float, bool)):
            cast_value = value
        elif value is not None:
            cast_value = str(value)
        return self._caster.to_float(cast_value)

    def get_str_list(self, key: str) -> list[str]:
        value = self.get_value(key)
        if isinstance(value, list):
            return [str(v) for v in value]
        if value is not None:
            return [str(value)]
        return []


class AnswerLookup(AnswerLookupMixin):
    def __init__(
        self, 
        answers: Sequence[UserAnswer], 
        caster: ValueCasterProtocol | None = None,
    ) -> None:
        self.answers = answers
        self._caster = caster or LenientCaster()

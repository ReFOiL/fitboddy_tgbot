"""
Factory для построения UserAnswer из ответов пользователя (Factory Pattern).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.questionnaire import CustomQuestion
from src.domain.entities.user_answer import UserAnswer
from src.domain.value_objects.questionnaire import AnswerType


class AnswerBuilder(ABC):
    """Базовый интерфейс для построения ответов."""

    @abstractmethod
    def build(
        self,
        user_id: int,
        question: CustomQuestion,
        value: str | int | bool | list[str] | None,
    ) -> list[UserAnswer]:
        """
        Построить список UserAnswer из значения.
        
        Args:
            user_id: ID пользователя
            question: Вопрос
            value: Значение ответа
            
        Returns:
            Список UserAnswer
        """
        pass

    @abstractmethod
    def can_handle(self, answer_type: AnswerType) -> bool:
        """Проверить, может ли builder обработать данный тип ответа."""
        pass


class SingleChoiceAnswerBuilder(AnswerBuilder):
    """Builder для SINGLE_CHOICE ответов."""

    def can_handle(self, answer_type: AnswerType) -> bool:
        return answer_type == AnswerType.SINGLE_CHOICE

    def build(
        self,
        user_id: int,
        question: CustomQuestion,
        value: str | int | bool | list[str] | None,
    ) -> list[UserAnswer]:
        if value is None:
            return []

        options_by_value = {opt.value: opt.id for opt in question.options}
        option_id = options_by_value.get(str(value))
        if option_id is None:
            return []

        return [UserAnswer(user_id=user_id, question_id=question.id, option_id=option_id)]


class MultipleChoiceAnswerBuilder(AnswerBuilder):
    """Builder для MULTIPLE_CHOICE ответов."""

    def can_handle(self, answer_type: AnswerType) -> bool:
        return answer_type == AnswerType.MULTIPLE_CHOICE

    def build(
        self,
        user_id: int,
        question: CustomQuestion,
        value: str | int | bool | list[str] | None,
    ) -> list[UserAnswer]:
        if value is None or not isinstance(value, list):
            return []

        options_by_value = {opt.value: opt.id for opt in question.options}
        answers: list[UserAnswer] = []

        for item in value:
            option_id = options_by_value.get(str(item))
            if option_id is None:
                continue
            answers.append(
                UserAnswer(user_id=user_id, question_id=question.id, option_id=option_id)
            )

        return answers


class TextAnswerBuilder(AnswerBuilder):
    """Builder для текстовых ответов (TEXT, NUMBER, etc.)."""

    def can_handle(self, answer_type: AnswerType) -> bool:
        return answer_type in {
            AnswerType.TEXT,
            AnswerType.NUMBER,
            AnswerType.BOOLEAN,
        }

    def build(
        self,
        user_id: int,
        question: CustomQuestion,
        value: str | int | bool | list[str] | None,
    ) -> list[UserAnswer]:
        if value is None:
            return []

        return [UserAnswer(user_id=user_id, question_id=question.id, value=value)]


class AnswerBuilderFactory:
    """Factory для создания подходящего AnswerBuilder."""

    def __init__(self, builders: list[AnswerBuilder] | None = None) -> None:
        """
        Args:
            builders: Список builders (по умолчанию создаются стандартные)
        """
        self._builders = builders or self._create_default_builders()

    def _create_default_builders(self) -> list[AnswerBuilder]:
        """Создать builders по умолчанию."""
        return [
            SingleChoiceAnswerBuilder(),
            MultipleChoiceAnswerBuilder(),
            TextAnswerBuilder(),
        ]

    def get_builder(self, answer_type: AnswerType) -> AnswerBuilder:
        """
        Получить подходящий builder для типа ответа.
        
        Args:
            answer_type: Тип ответа
            
        Returns:
            Подходящий builder
            
        Raises:
            ValueError: Если не найден подходящий builder
        """
        for builder in self._builders:
            if builder.can_handle(answer_type):
                return builder

        raise ValueError(f"No builder found for answer type: {answer_type}")

    def build_answers(
        self,
        user_id: int,
        question: CustomQuestion,
        value: str | int | bool | list[str] | None,
    ) -> list[UserAnswer]:
        """
        Построить список UserAnswer используя подходящий builder.
        
        Args:
            user_id: ID пользователя
            question: Вопрос
            value: Значение ответа
            
        Returns:
            Список UserAnswer
        """
        builder = self.get_builder(question.answer_type)
        return builder.build(user_id, question, value)

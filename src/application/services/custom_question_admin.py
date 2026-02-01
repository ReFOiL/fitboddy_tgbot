from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption


class CustomQuestionAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._option_factory = CustomQuestionOptionFactory()

    async def list_all(self) -> list[CustomQuestion]:
        async with self._uow:
            return await self._uow.custom_questions.list_all()

    async def create(self, payload: dict[str, object]) -> CustomQuestion:
        async with self._uow:
            options = payload.pop("options", None)
            question = CustomQuestion(**payload)
            if isinstance(options, list):
                question.options = self._option_factory.build(options)
            await self._uow.custom_questions.add(question)
            await self._uow.commit()
            return question

    async def update(self, question_id: int, updates: dict[str, object]) -> CustomQuestion:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            options = updates.pop("options", None)
            for key, value in updates.items():
                setattr(question, key, value)
            if isinstance(options, list):
                question.options = self._option_factory.build(options)
            await self._uow.commit()
            return question

    async def deactivate(self, question_id: int) -> None:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            question.is_active = False
            await self._uow.commit()

    async def update_order(self, question_id: int, new_order: int) -> None:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            question.order = new_order
            await self._uow.commit()

    async def link_template(self, question_id: int, template_id: int) -> None:
        async with self._uow:
            await self._uow.question_template_links.add(
                question_id=question_id, template_id=template_id
            )
            await self._uow.commit()


class CustomQuestionOptionFactory:
    def build(self, options: list[dict[str, object]]) -> list[CustomQuestionOption]:
        items: list[CustomQuestionOption] = []
        for idx, option in enumerate(options, start=1):
            value = str(option.get("value", "")).strip()
            label = str(option.get("label", value)).strip()
            if not value:
                continue
            items.append(CustomQuestionOption(value=value, label=label, sort_order=idx))
        return items

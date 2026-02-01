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

            # Insert into correct position and resequence all active questions.
            questions = await self._uow.custom_questions.list_active_ordered()
            desired_order = int(payload.get("order") or (len(questions) + 1))
            self._insert_and_resequence(questions, question, desired_order)

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
            questions = await self._uow.custom_questions.list_active_ordered()
            target_idx = next((i for i, q in enumerate(questions) if q.id == question_id), None)
            if target_idx is None:
                raise ValueError("Question not found")

            # Move element to 1-based new_order position, then renumber all sequentially.
            moved = questions.pop(target_idx)
            systems = [q for q in questions if self._is_system(q)]
            if self._is_system(moved):
                # System questions can only live inside system block.
                new_idx = max(0, min(len(systems), new_order - 1))
            else:
                # Custom questions must always stay after system questions.
                new_idx = max(len(systems), min(len(questions), new_order - 1))
            questions.insert(new_idx, moved)
            for idx, q in enumerate(questions, start=1):
                q.order = idx

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


    @staticmethod
    def _is_system(question: CustomQuestion) -> bool:
        return bool(question.key) and question.key.startswith("system:")

    def _insert_and_resequence(self, existing: list[CustomQuestion], new_question: CustomQuestion, desired_order: int) -> None:
        systems = [q for q in existing if self._is_system(q)]
        new_question_is_system = self._is_system(new_question)

        # Insert position is 1-based in API; convert to 0-based and clamp.
        if new_question_is_system:
            min_idx = 0
            max_idx = len(systems)
        else:
            min_idx = len(systems)
            max_idx = len(existing)
        new_idx = max(min_idx, min(max_idx, desired_order - 1))

        existing.insert(new_idx, new_question)
        for idx, q in enumerate(existing, start=1):
            q.order = idx

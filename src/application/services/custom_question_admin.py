from __future__ import annotations

from typing import ClassVar, cast

from src.application.interfaces.repositories import UnitOfWork
from src.commons.exceptions import SystemQuestionMutationError
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption, CustomQuestionScoringWeight


class CustomQuestionAdminService:
    """Поля, которые безопасно править у системных вопросов (не ломают матчинг по ключам/значениям)."""

    SYSTEM_QUESTION_MUTABLE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"text", "order", "category", "tags"}
    )

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._option_factory = CustomQuestionOptionFactory()

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

    async def list_all(self) -> list[CustomQuestion]:
        async with self._uow:
            return await self._uow.custom_questions.list_all()

    async def create(self, payload: dict[str, str | int | float | bool | None | list[dict[str, str]]]) -> CustomQuestion:
        match payload.get("key"):
            case str(raw_key) if raw_key.strip().startswith("system:"):
                raise SystemQuestionMutationError(
                    "Создавать вопросы с ключом system:* через админку нельзя — они задаются сидом/релизом."
                )
            case _:
                pass
        async with self._uow:
            options = payload.pop("options", None)
            question = CustomQuestion(**payload)
            match options:
                case list(opts):
                    question.options = self._option_factory.build(cast(list[dict[str, str]], opts))
                case None:
                    pass
                case _:
                    raise SystemQuestionMutationError("Поле options должно быть списком опций или отсутствовать.")

            # Insert into correct position and resequence all active questions.
            questions = await self._uow.custom_questions.list_active_ordered()
            order_value = payload.get("order")
            desired_order = int(order_value) if order_value is not None else (len(questions) + 1)
            self._insert_and_resequence(questions, question, desired_order)

            await self._uow.custom_questions.add(question)
            await self._uow.commit()
            return question

    async def update(self, question_id: int, updates: dict[str, str | int | float | bool | None | list[dict[str, str]]]) -> CustomQuestion:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            new_key = updates.get("key")
            match new_key:
                case str(s) if s.strip().startswith("system:") and not self._is_system(question):
                    raise SystemQuestionMutationError("Нельзя назначить ключ system:* обычному вопросу.")
                case str(s) if self._is_system(question) and s.strip() != question.key:
                    raise SystemQuestionMutationError("Нельзя менять ключ системного вопроса.")
                case str() | None:
                    pass
                case _:
                    raise SystemQuestionMutationError("Поле key должно быть строкой.")

            if self._is_system(question):
                mutable = type(self).SYSTEM_QUESTION_MUTABLE_FIELDS
                forbidden = [k for k in updates if k not in mutable]
                if forbidden:
                    allowed = ", ".join(sorted(mutable))
                    raise SystemQuestionMutationError(
                        f"Системный вопрос можно менять только в полях: {allowed}. Запрещено: {', '.join(forbidden)}."
                    )

            options = updates.pop("options", None)
            for key, value in updates.items():
                setattr(question, key, value)
            match options:
                case list(opts):
                    question.options = self._option_factory.build(cast(list[dict[str, str]], opts))
                case None:
                    pass
                case _:
                    raise SystemQuestionMutationError("Поле options должно быть списком опций или отсутствовать.")
            await self._uow.commit()
            return question

    async def deactivate(self, question_id: int) -> None:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            if self._is_system(question):
                raise SystemQuestionMutationError(
                    "Системный вопрос (ключ system:*) нельзя деактивировать — на нём завязан подбор тренировок."
                )
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

    async def list_scoring_weights(self, question_id: int) -> list[CustomQuestionScoringWeight]:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            return question.scoring_weights or []

    async def create_or_update_scoring_weight(
        self, question_id: int, answer_value: str, weight: int
    ) -> CustomQuestionScoringWeight:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            
            # Ищем существующий вес
            existing_weight = None
            if question.scoring_weights:
                for sw in question.scoring_weights:
                    if sw.answer_value == answer_value:
                        existing_weight = sw
                        break
            
            if existing_weight:
                existing_weight.weight = weight
                await self._uow.commit()
                return existing_weight
            else:
                new_weight = CustomQuestionScoringWeight(
                    question_id=question_id,
                    answer_value=answer_value,
                    weight=weight,
                )
                question.scoring_weights.append(new_weight)
                await self._uow.flush()
                await self._uow.commit()
                return new_weight

    async def delete_scoring_weight(self, question_id: int, answer_value: str) -> None:
        async with self._uow:
            question = await self._uow.custom_questions.get(question_id)
            if question is None:
                raise ValueError("Question not found")
            
            if question.scoring_weights:
                weight_to_remove = None
                for sw in question.scoring_weights:
                    if sw.answer_value == answer_value:
                        weight_to_remove = sw
                        break
                
                if weight_to_remove:
                    question.scoring_weights.remove(weight_to_remove)
                    await self._uow.commit()
                else:
                    raise ValueError(f"Weight for answer_value '{answer_value}' not found")


class CustomQuestionOptionFactory:
    def build(self, options: list[dict[str, str]]) -> list[CustomQuestionOption]:
        items: list[CustomQuestionOption] = []
        for idx, option in enumerate(options, start=1):
            value = str(option.get("value", "")).strip()
            label = str(option.get("label", value)).strip()
            if not value:
                continue
            items.append(CustomQuestionOption(value=value, label=label, sort_order=idx))
        return items

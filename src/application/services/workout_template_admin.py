"""Админ-сервис: CRUD шаблонов тренировок и привязка упражнений."""
from __future__ import annotations

from typing import TypedDict

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.associations import WorkoutExercise
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate


class ExerciseLink(TypedDict, total=False):
    exercise_id: int
    sort_order: int
    sets: int | None
    reps: int | None
    duration_seconds: int | None
    rest_seconds: int | None
    notes: str | None


class WorkoutTemplateAdminService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_all(self) -> list[WorkoutTemplate]:
        async with self._uow:
            return await self._uow.workouts.list_all()

    async def get_by_id(self, template_id: int) -> WorkoutTemplate | None:
        async with self._uow:
            return await self._uow.workouts.get_by_id(template_id)

    async def create(
        self,
        *,
        title: str,
        goal: str,
        difficulty: WorkoutDifficulty,
        equipment: str | None = None,
        days_per_week: int = 3,
        description: str | None = None,
        is_active: bool = True,
        user_id: int | None = None,
        exercises: list[ExerciseLink] | None = None,
    ) -> WorkoutTemplate:
        async with self._uow:
            template = WorkoutTemplate(
                title=title,
                goal=goal,
                difficulty=difficulty,
                equipment=equipment,
                days_per_week=days_per_week,
                description=description,
                is_active=is_active,
                user_id=user_id,
            )
            await self._uow.workouts.add(template)
            await self._uow.flush()
            if exercises:
                for link in exercises:
                    ex_id = link["exercise_id"]
                    exercise = await self._uow.exercises.get_by_id(ex_id)
                    if exercise is None:
                        continue
                    we = WorkoutExercise(
                        workout_id=template.id,
                        exercise_id=ex_id,
                        sort_order=link.get("sort_order", 0),
                        sets=link.get("sets"),
                        reps=link.get("reps"),
                        duration_seconds=link.get("duration_seconds"),
                        rest_seconds=link.get("rest_seconds"),
                        notes=link.get("notes"),
                    )
                    we.exercise = exercise
                    template.workout_exercises.append(we)
            await self._uow.commit()
        return template

    async def update(
        self,
        template_id: int,
        *,
        exercises: list[ExerciseLink] | None = None,
        **scalar_updates: object,
    ) -> WorkoutTemplate | None:
        async with self._uow:
            template = await self._uow.workouts.get_by_id(template_id)
            if template is None:
                return None
            for key, value in scalar_updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            if exercises is not None:
                template.workout_exercises.clear()
                for link in exercises:
                    ex_id = link["exercise_id"]
                    exercise = await self._uow.exercises.get_by_id(ex_id)
                    if exercise is None:
                        continue
                    we = WorkoutExercise(
                        workout_id=template.id,
                        exercise_id=ex_id,
                        sort_order=link.get("sort_order", 0),
                        sets=link.get("sets"),
                        reps=link.get("reps"),
                        duration_seconds=link.get("duration_seconds"),
                        rest_seconds=link.get("rest_seconds"),
                        notes=link.get("notes"),
                    )
                    we.exercise = exercise
                    template.workout_exercises.append(we)
            await self._uow.commit()
        return template

    async def update_exercises_order(
        self, template_id: int, exercise_ids: list[int]
    ) -> WorkoutTemplate | None:
        async with self._uow:
            template = await self._uow.workouts.get_by_id(template_id)
            if template is None:
                return None
            by_exercise_id = {we.exercise_id: we for we in template.workout_exercises}
            if len(exercise_ids) != len(by_exercise_id) or any(
                eid not in by_exercise_id for eid in exercise_ids
            ):
                return None
            for sort_order, ex_id in enumerate(exercise_ids):
                by_exercise_id[ex_id].sort_order = sort_order
            await self._uow.commit()
            template = await self._uow.workouts.get_by_id(template_id)
        return template

    async def delete(self, template_id: int) -> bool:
        async with self._uow:
            template = await self._uow.workouts.get_by_id(template_id)
            if template is None:
                return False
            await self._uow.workouts.delete(template_id)
            await self._uow.commit()
        return True

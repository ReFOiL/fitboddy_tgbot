from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.services.scheduled_workout_lines import ordered_lines
from src.application.use_cases.workout.base import WorkoutUseCaseMetrics
from src.application.use_cases.workout.callback.errors import (
    CallbackExerciseReplacementNotAvailableError,
    CallbackWorkoutAlreadyCompletedError,
    CallbackWorkoutNotFoundError,
)
from src.application.use_cases.workout.callback.models import (
    ReplaceWorkoutExerciseRequest,
    ReplaceWorkoutExerciseResult,
)
from src.application.use_cases.workout.callback.resolver import WorkoutCallbackResolver
from src.domain.entities.exercise import Exercise


class ReplaceWorkoutExerciseUseCase(WorkoutUseCaseMetrics):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._resolver = WorkoutCallbackResolver(uow)

    async def replace(self, request: ReplaceWorkoutExerciseRequest) -> ReplaceWorkoutExerciseResult:
        async def _operation() -> ReplaceWorkoutExerciseResult:
            if request.index < 1:
                raise CallbackWorkoutNotFoundError()
            async with self._uow:
                user_id = await self._resolver.resolve_user_id(request.tg_user_id)
                workout = await self._resolver.get_scheduled_for_user(user_id, request.scheduled_id)
                if workout.is_completed:
                    raise CallbackWorkoutAlreadyCompletedError()
                rows = ordered_lines(workout)
                if request.index > len(rows):
                    raise CallbackWorkoutNotFoundError()
                line = rows[request.index - 1]
                current_exercise = line.exercise
                if current_exercise is None:
                    raise CallbackWorkoutNotFoundError()

                alternatives = await self._find_alternatives(
                    current_exercise=current_exercise,
                    existing_exercise_ids={item.exercise_id for item in rows},
                )
                if not alternatives:
                    raise CallbackExerciseReplacementNotAvailableError()
                replacement = alternatives[0]

                line.exercise_id = replacement.id
                line.exercise = replacement
                await self._uow.commit()
                return ReplaceWorkoutExerciseResult(
                    user_id=user_id,
                    scheduled_id=request.scheduled_id,
                    index=request.index,
                    previous_exercise_name=current_exercise.name,
                    replacement_exercise_name=replacement.name,
                )

        return await self.run_with_metrics("replace_workout_exercise", _operation)

    async def _find_alternatives(
        self,
        *,
        current_exercise: Exercise,
        existing_exercise_ids: set[int],
    ) -> list[Exercise]:
        exercises = await self._uow.exercises.list_all()
        primary = [
            exercise
            for exercise in exercises
            if self._is_candidate(
                exercise=exercise,
                current_exercise=current_exercise,
                existing_exercise_ids=existing_exercise_ids,
                require_same_category=True,
            )
        ]
        if primary:
            return primary
        return [
            exercise
            for exercise in exercises
            if self._is_candidate(
                exercise=exercise,
                current_exercise=current_exercise,
                existing_exercise_ids=existing_exercise_ids,
                require_same_category=False,
            )
        ]

    @staticmethod
    def _is_candidate(
        *,
        exercise: Exercise,
        current_exercise: Exercise,
        existing_exercise_ids: set[int],
        require_same_category: bool,
    ) -> bool:
        if exercise.id in existing_exercise_ids or exercise.id == current_exercise.id:
            return False
        if exercise.is_cardio != current_exercise.is_cardio:
            return False
        if require_same_category and exercise.workout_category != current_exercise.workout_category:
            return False
        return True

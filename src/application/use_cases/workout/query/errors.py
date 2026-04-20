from __future__ import annotations


class WorkoutQueryError(RuntimeError):
    pass


class WorkoutQueryUserNotFound(WorkoutQueryError):
    pass


class WorkoutQueryPlanNotFound(WorkoutQueryError):
    pass


class WorkoutQueryTodayWorkoutNotFound(WorkoutQueryError):
    pass


class WorkoutQueryAlreadyCompleted(WorkoutQueryError):
    pass


class WorkoutQueryExerciseNotFound(WorkoutQueryError):
    pass


class WorkoutQueryAccessDenied(WorkoutQueryError):
    pass

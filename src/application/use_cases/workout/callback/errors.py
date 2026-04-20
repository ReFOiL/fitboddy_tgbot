from __future__ import annotations


class WorkoutCallbackError(RuntimeError):
    pass


class CallbackUserNotFoundError(WorkoutCallbackError):
    pass


class CallbackWorkoutNotFoundError(WorkoutCallbackError):
    pass


class CallbackWorkoutAccessDeniedError(WorkoutCallbackError):
    pass


class CallbackWorkoutAlreadyCompletedError(WorkoutCallbackError):
    pass

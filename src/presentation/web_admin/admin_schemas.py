"""
Pydantic-схемы ответов и тел запросов админского REST API
(упражнения, справочники, планы — роутеры `api/v1`).
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.training_plan import TrainingPlanStatus


class MessageOut(BaseModel):
    message: str


# --- Muscle (справочник) ---
class MuscleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int


class MuscleCreate(BaseModel):
    name: str = Field(..., max_length=64)
    sort_order: int = Field(default=0, ge=0)


class MuscleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    sort_order: int | None = Field(default=None, ge=0)


# --- Contraindication (справочник) ---
class ContraindicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int


class ContraindicationCreate(BaseModel):
    name: str = Field(..., max_length=64)
    sort_order: int = Field(default=0, ge=0)


class ContraindicationUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    sort_order: int | None = Field(default=None, ge=0)


# --- Exercise (связь с мышцами и противопоказаниями по id) ---
class ExerciseCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    video_url: str | None = Field(default=None, max_length=500)
    muscle_ids: list[int] = Field(default_factory=list)
    equipment: str | None = Field(default=None, max_length=64)
    is_cardio: bool = False
    difficulty: int = Field(default=1, ge=1, le=5)
    contraindication_ids: list[int] = Field(default_factory=list)
    workout_category: str = Field(default="full_body", max_length=50)


class ExerciseUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    video_url: str | None = Field(default=None, max_length=500)
    muscle_ids: list[int] | None = None
    equipment: str | None = Field(default=None, max_length=64)
    is_cardio: bool | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    contraindication_ids: list[int] | None = None
    workout_category: str | None = Field(default=None, max_length=50)


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    video_url: str | None
    video_stream_url: str | None = None
    muscles: list[MuscleOut] = Field(default_factory=list)
    equipment: str | None
    is_cardio: bool
    difficulty: int
    workout_category: str
    contraindications: list[ContraindicationOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ScheduledWorkoutExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scheduled_workout_id: int
    exercise_id: int
    sort_order: int
    sets: int | None
    reps: int | None
    duration_seconds: int | None
    rest_seconds: int | None
    exercise: ExerciseOut


class TrainingPlanCreate(BaseModel):
    user_id: int
    start_date: date
    end_date: date
    status: TrainingPlanStatus = TrainingPlanStatus.ACTIVE


class TrainingPlanUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: TrainingPlanStatus | None = None


class TrainingPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    start_date: date
    end_date: date
    status: TrainingPlanStatus
    created_at: datetime

    scheduled_workouts: list["ScheduledWorkoutOut"] = Field(default_factory=list)


class ScheduledWorkoutCreate(BaseModel):
    plan_id: int
    scheduled_for: date
    week: int | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    volume_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)


class ScheduledWorkoutUpdate(BaseModel):
    scheduled_for: date | None = None
    week: int | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    volume_multiplier: float | None = Field(default=None, ge=0.1, le=10.0)
    is_completed: bool | None = None
    completed_at: datetime | None = None
    perceived_effort: str | None = Field(
        default=None,
        max_length=16,
        description="easy | ok | hard; пустая строка — сброс",
    )


class ScheduledWorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    scheduled_for: date
    week: int | None
    day_of_week: int | None
    volume_multiplier: float
    is_completed: bool
    completed_at: datetime | None
    perceived_effort: str | None = None

    session_exercises: list[ScheduledWorkoutExerciseOut] = Field(default_factory=list)


class TrainingPlanListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    start_date: date
    end_date: date
    status: TrainingPlanStatus
    created_at: datetime


class SessionExerciseLineIn(BaseModel):
    exercise_id: int
    sort_order: int = Field(..., ge=0)
    sets: int | None = Field(default=None, ge=1, le=50)
    reps: int | None = Field(default=None, ge=1, le=200)
    duration_seconds: int | None = Field(default=None, ge=1)
    rest_seconds: int | None = Field(default=None, ge=0)


class ReplaceSessionExercisesIn(BaseModel):
    exercises: list[SessionExerciseLineIn] = Field(..., min_length=1)

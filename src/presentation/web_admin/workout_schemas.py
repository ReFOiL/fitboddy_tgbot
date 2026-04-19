from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from src.domain.entities.training_plan import TrainingPlanStatus
from src.domain.entities.workout import WorkoutDifficulty
import enum


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


class ExerciseUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    video_url: str | None = Field(default=None, max_length=500)
    muscle_ids: list[int] | None = None
    equipment: str | None = Field(default=None, max_length=64)
    is_cardio: bool | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    contraindication_ids: list[int] | None = None


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
    contraindications: list[ContraindicationOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    sort_order: int = 0
    sets: int | None = Field(default=None, ge=1, le=50)
    reps: int | None = Field(default=None, ge=1, le=200)
    duration_seconds: int | None = Field(default=None, ge=1, le=60 * 60)
    rest_seconds: int | None = Field(default=None, ge=0, le=60 * 60)
    notes: str | None = Field(default=None, max_length=500)


class WorkoutExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workout_id: int
    exercise_id: int
    sort_order: int
    sets: int | None
    reps: int | None
    duration_seconds: int | None
    rest_seconds: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    exercise: ExerciseOut


class WorkoutCategory(str, enum.Enum):
    """Категории тренировок."""
    FULL_BODY = "full_body"
    UPPER = "upper"
    LOWER = "lower"
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    CARDIO = "cardio"


class WorkoutTemplateCreate(BaseModel):
    title: str = Field(..., max_length=128)
    goal: str = Field(..., max_length=32)
    difficulty: WorkoutDifficulty
    days_per_week: int = Field(default=3, ge=1, le=7)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True
    user_id: int | None = None
    exercises: list[WorkoutExerciseCreate] = Field(default_factory=list)
    # Новые поля
    required_equipment_ids: list[int] = Field(default_factory=list)
    intensity_factor: float = Field(default=1.0, ge=0.1, le=5.0)
    workout_category: WorkoutCategory = WorkoutCategory.FULL_BODY
    min_age: int | None = Field(default=None, ge=0, le=150)
    max_age: int | None = Field(default=None, ge=0, le=150)


class WorkoutTemplateUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=128)
    goal: str | None = Field(default=None, max_length=32)
    difficulty: WorkoutDifficulty | None = None
    days_per_week: int | None = Field(default=None, ge=1, le=7)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    user_id: int | None = None
    exercises: list[WorkoutExerciseCreate] | None = None
    # Новые поля
    required_equipment_ids: list[int] | None = None
    intensity_factor: float | None = Field(default=None, ge=0.1, le=5.0)
    workout_category: WorkoutCategory | None = None
    min_age: int | None = Field(default=None, ge=0, le=150)
    max_age: int | None = Field(default=None, ge=0, le=150)


class WorkoutExercisesOrderUpdate(BaseModel):
    exercise_ids: list[int] = Field(..., min_length=1)


class WorkoutTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    goal: str
    difficulty: WorkoutDifficulty
    days_per_week: int
    user_id: int | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Новые поля
    intensity_factor: float
    workout_category: str
    min_age: int | None
    max_age: int | None

    workout_exercises: list[WorkoutExerciseOut] = Field(default_factory=list)
    # Новые связи (будут заполняться через контроллер)
    required_equipment: list["EquipmentOut"] = Field(default_factory=list)


# Forward references для EquipmentOut
from src.presentation.web_admin.equipment_schemas import EquipmentOut  # noqa: E402


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
    template_id: int | None = None
    scheduled_for: date
    week: int | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    volume_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)


class ScheduledWorkoutUpdate(BaseModel):
    template_id: int | None = None
    scheduled_for: date | None = None
    week: int | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    volume_multiplier: float | None = Field(default=None, ge=0.1, le=10.0)
    is_completed: bool | None = None
    completed_at: datetime | None = None


class ScheduledWorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    template_id: int | None
    scheduled_for: date
    week: int | None
    day_of_week: int | None
    volume_multiplier: float
    is_completed: bool
    completed_at: datetime | None

    template: WorkoutTemplateOut | None


from __future__ import annotations

from src.domain.value_objects.anthropometry import Anthropometry
from src.domain.value_objects.kcju import Kcju
from src.domain.value_objects.workout_profile import TrainingGoal


def calculate_kcju(
    anthropometry: Anthropometry,
    activity_multiplier: float,
    goal: str,
) -> Kcju:
    if anthropometry.gender == "male":
        bmr = 10 * anthropometry.weight_kg + 6.25 * anthropometry.height_cm - 5 * anthropometry.age + 5
    else:
        bmr = 10 * anthropometry.weight_kg + 6.25 * anthropometry.height_cm - 5 * anthropometry.age - 161

    calories = int(bmr * activity_multiplier)

    normalized_goal = TrainingGoal.from_raw(goal)
    if normalized_goal == TrainingGoal.WEIGHT_LOSS:
        calories = int(calories * 0.85)
    elif normalized_goal == TrainingGoal.MUSCLE_GAIN:
        calories = int(calories * 1.1)

    protein = int(anthropometry.weight_kg * 2.0)
    fat = int(anthropometry.weight_kg * 0.9)
    carbs = max(int((calories - protein * 4 - fat * 9) / 4), 0)

    return Kcju(calories=calories, protein_g=protein, fat_g=fat, carbs_g=carbs)


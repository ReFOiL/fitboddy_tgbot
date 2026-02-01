import pytest  # type: ignore[import-not-found]

from src.application.use_cases.workout_generator.simple_matcher import SimpleWorkoutMatcher
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate


@pytest.mark.asyncio  # type: ignore[misc]
async def test_simple_matcher_returns_workouts() -> None:
    answers = [
        UserAnswer(user_id=1, question_key="system:goal", value="weight_loss"),
        UserAnswer(user_id=1, question_key="system:level", value="beginner"),
        UserAnswer(user_id=1, question_key="system:workout_location", value="home"),
        UserAnswer(user_id=1, question_key="system:workouts_per_week", value=3),
        UserAnswer(user_id=1, question_key="system:equipment", value=["none"]),
    ]

    templates = [
        WorkoutTemplate(title="Cardio Beginner", goal="weight_loss", difficulty=WorkoutDifficulty.LOW, equipment="none", days_per_week=3),
        WorkoutTemplate(title="Strength Beginner", goal="muscle_gain", difficulty=WorkoutDifficulty.LOW, equipment="dumbbells", days_per_week=3),
    ]

    matcher = SimpleWorkoutMatcher()
    result = await matcher.match(answers, templates)
    assert result


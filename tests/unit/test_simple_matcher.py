import pytest  # type: ignore[import-not-found]

from src.application.use_cases.workout_generator.simple_matcher import SimpleWorkoutMatcher
from src.domain.entities.user_answer import UserAnswer
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate
from src.domain.entities.questionnaire import CustomQuestion
from src.domain.value_objects.questionnaire import AnswerType


@pytest.mark.asyncio  # type: ignore[misc]
async def test_simple_matcher_returns_workouts() -> None:
    # Создаём вопросы для ответов
    goal_question: CustomQuestion = CustomQuestion(
        id=1, key="system:goal", text="Цель", answer_type=AnswerType.SINGLE_CHOICE
    )
    level_question: CustomQuestion = CustomQuestion(
        id=2, key="system:level", text="Уровень", answer_type=AnswerType.SINGLE_CHOICE
    )
    location_question: CustomQuestion = CustomQuestion(
        id=3, key="system:workout_location", text="Место", answer_type=AnswerType.SINGLE_CHOICE
    )
    per_week_question: CustomQuestion = CustomQuestion(
        id=4, key="system:workouts_per_week", text="Тренировок в неделю", answer_type=AnswerType.NUMBER
    )
    equipment_question: CustomQuestion = CustomQuestion(
        id=5, key="system:equipment", text="Оборудование", answer_type=AnswerType.MULTIPLE_CHOICE
    )
    
    answers = [
        UserAnswer(user_id=1, question_id=1, value="weight_loss"),
        UserAnswer(user_id=1, question_id=2, value="beginner"),
        UserAnswer(user_id=1, question_id=3, value="home"),
        UserAnswer(user_id=1, question_id=4, value=3),
        UserAnswer(user_id=1, question_id=5, value=["none"]),
    ]
    
    # Привязываем вопросы к ответам
    answers[0].question = goal_question
    answers[1].question = level_question
    answers[2].question = location_question
    answers[3].question = per_week_question
    answers[4].question = equipment_question

    templates = [
        WorkoutTemplate(
            title="Cardio Beginner",
            goal="weight_loss",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="cardio",
            is_active=True,
        ),
        WorkoutTemplate(
            title="Strength Beginner",
            goal="muscle_gain",
            difficulty=WorkoutDifficulty.LOW,
            days_per_week=3,
            intensity_factor=1.0,
            workout_category="full_body",
            is_active=True,
        ),
    ]

    matcher = SimpleWorkoutMatcher()
    result = await matcher.match(answers, templates)
    assert result


from __future__ import annotations

from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption
from src.domain.value_objects.questionnaire import AnswerType
from src.domain.value_objects.questionnaire_system import SystemQuestionKey
from src.domain.value_objects.workout_profile import EquipmentName, TrainingGoal, WorkoutLocation


class CustomQuestionSeedCatalog:
    """Системные вопросы MVP + один пример кастомного (травмы/ограничения)."""

    def system_questions(self) -> list[CustomQuestion]:
        return [
            CustomQuestion(
                is_system=True,
                key=SystemQuestionKey.GOAL,
                order=1,
                text="Какая у вас основная цель тренировок?",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value=TrainingGoal.WEIGHT_LOSS, label="Похудение", sort_order=1),
                    CustomQuestionOption(
                        value=TrainingGoal.MUSCLE_GAIN,
                        label="Набор мышечной массы",
                        sort_order=2,
                    ),
                    CustomQuestionOption(value=TrainingGoal.ENDURANCE, label="Повышение выносливости", sort_order=3),
                    CustomQuestionOption(value=TrainingGoal.MAINTENANCE, label="Поддержание формы", sort_order=4),
                    CustomQuestionOption(value=TrainingGoal.REHABILITATION, label="Реабилитация", sort_order=5),
                ],
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key="system:level",
                order=2,
                text="Ваш уровень подготовки?",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(
                        value="beginner",
                        label="Новичок (0–6 месяцев регулярных тренировок)",
                        sort_order=1,
                    ),
                    CustomQuestionOption(
                        value="intermediate",
                        label="Средний (6–24 месяца)",
                        sort_order=2,
                    ),
                    CustomQuestionOption(
                        value="advanced",
                        label="Продвинутый (более 2 лет)",
                        sort_order=3,
                    ),
                ],
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key=SystemQuestionKey.WORKOUT_LOCATION,
                order=3,
                text="Где вы планируете тренироваться?",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value=WorkoutLocation.HOME, label="Дома", sort_order=1),
                    CustomQuestionOption(value=WorkoutLocation.GYM, label="В фитнес-зале", sort_order=2),
                    CustomQuestionOption(value=WorkoutLocation.BOTH, label="И дома, и в зале", sort_order=3),
                ],
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key=SystemQuestionKey.EQUIPMENT,
                order=4,
                text="Какое оборудование у вас есть?",
                answer_type=AnswerType.MULTIPLE_CHOICE,
                options=[
                    CustomQuestionOption(value=EquipmentName.DUMBBELLS, label="Гантели", sort_order=1),
                    CustomQuestionOption(value=EquipmentName.BARBELL, label="Штанга", sort_order=2),
                    CustomQuestionOption(value=EquipmentName.RESISTANCE_BANDS, label="Резинки / эспандеры", sort_order=3),
                    CustomQuestionOption(value=EquipmentName.KETTLEBELL, label="Гиря", sort_order=4),
                    CustomQuestionOption(value=EquipmentName.TREADMILL, label="Беговая дорожка", sort_order=5),
                    CustomQuestionOption(value=EquipmentName.OTHER, label="Другое", sort_order=6),
                    CustomQuestionOption(value=EquipmentName.NONE, label="Нет оборудования", sort_order=7),
                ],
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key=SystemQuestionKey.WORKOUTS_PER_WEEK,
                order=5,
                text="Сколько тренировок в неделю вы хотите проводить?",
                answer_type=AnswerType.NUMBER,
                min_value=1,
                max_value=7,
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key="system:age",
                order=6,
                text="Сколько вам лет?",
                answer_type=AnswerType.NUMBER,
                min_value=16,
                max_value=100,
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key="system:gender",
                order=7,
                text="Ваш пол?",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="male", label="Мужской", sort_order=1),
                    CustomQuestionOption(value="female", label="Женский", sort_order=2),
                ],
                is_required=True,
            ),
        ]

    def mvp_custom_question(self) -> CustomQuestion:
        return CustomQuestion(
            key="custom:health_notes",
            order=8,
            text="Есть ли травмы или ограничения, о которых нужно знать при подборе упражнений? Опишите кратко.",
            answer_type=AnswerType.TEXT,
            is_required=False,
            category="health_info",
            tags=["injury", "constraint"],
        )

from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout_generator.seed_templates import get_default_templates
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption
from src.domain.value_objects.questionnaire import AnswerType


class WorkoutTemplateSeeder:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def run(self) -> int:
        async with self._uow:
            existing = await self._uow.workouts.list_all()
            if existing:
                return 0
            templates = get_default_templates()
            for template in templates:
                await self._uow.workouts.add(template)
            await self._uow.commit()
            return len(templates)


class CustomQuestionSeedCatalog:
    def system_questions(self) -> list[CustomQuestion]:
        return [
            CustomQuestion(
                key="system:goal",
                order=1,
                text="Цель тренировок:",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="weight_loss", label="🔥 Похудение", sort_order=1),
                    CustomQuestionOption(value="muscle_gain", label="💪 Набор массы", sort_order=2),
                    CustomQuestionOption(value="endurance", label="🏃 Выносливость", sort_order=3),
                    CustomQuestionOption(value="maintenance", label="✅ Поддержание", sort_order=4),
                    CustomQuestionOption(value="rehabilitation", label="🩹 Реабилитация", sort_order=5),
                ],
                is_required=True,
            ),
            CustomQuestion(
                key="system:level",
                order=2,
                text="Уровень подготовки:",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="beginner", label="🟢 Новичок", sort_order=1),
                    CustomQuestionOption(value="intermediate", label="🟡 Средний", sort_order=2),
                    CustomQuestionOption(value="advanced", label="🔴 Продвинутый", sort_order=3),
                ],
                is_required=True,
            ),
            CustomQuestion(
                key="system:gender",
                order=3,
                text="Пол:",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="male", label="👨 Мужской", sort_order=1),
                    CustomQuestionOption(value="female", label="👩 Женский", sort_order=2),
                    CustomQuestionOption(value="other", label="🧑 Другое", sort_order=3),
                ],
                is_required=True,
            ),
            CustomQuestion(
                key="system:age",
                order=4,
                text="Возраст:",
                answer_type=AnswerType.NUMBER,
                min_value=16,
                max_value=70,
                is_required=True,
            ),
            CustomQuestion(
                key="system:height",
                order=5,
                text="Рост в см:",
                answer_type=AnswerType.NUMBER,
                min_value=120,
                max_value=230,
                is_required=True,
            ),
            CustomQuestion(
                key="system:weight",
                order=6,
                text="Вес в кг:",
                answer_type=AnswerType.NUMBER,
                min_value=30,
                max_value=250,
                is_required=True,
            ),
            CustomQuestion(
                key="system:activity",
                order=7,
                text="Активность:",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="sedentary", label="🪑 Сидячий", sort_order=1),
                    CustomQuestionOption(value="light", label="🚶 Легкая активность", sort_order=2),
                    CustomQuestionOption(value="moderate", label="🏃 Умеренная активность", sort_order=3),
                    CustomQuestionOption(value="active", label="🏋️ Активный", sort_order=4),
                    CustomQuestionOption(value="athlete", label="🏆 Профи", sort_order=5),
                ],
                is_required=True,
            ),
            CustomQuestion(
                key="system:equipment",
                order=8,
                text="Оборудование:",
                answer_type=AnswerType.MULTIPLE_CHOICE,
                options=[
                    CustomQuestionOption(value="dumbbells", label="🏋️ Гантели", sort_order=1),
                    CustomQuestionOption(value="barbell", label="🏋️‍♂️ Штанга", sort_order=2),
                    CustomQuestionOption(value="resistance_bands", label="🧵 Резинки", sort_order=3),
                    CustomQuestionOption(value="kettlebell", label="🏋️ Кеттлбелл", sort_order=4),
                    CustomQuestionOption(value="treadmill", label="🏃 Дорожка", sort_order=5),
                    CustomQuestionOption(value="none", label="🚫 Нет", sort_order=6),
                ],
                is_required=True,
            ),
            CustomQuestion(
                key="system:workouts_per_week",
                order=9,
                text="Тренировок в неделю:",
                answer_type=AnswerType.NUMBER,
                min_value=1,
                max_value=7,
                is_required=True,
            ),
            CustomQuestion(
                key="system:workout_location",
                order=10,
                text="Место тренировок:",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="home", label="🏠 Дом", sort_order=1),
                    CustomQuestionOption(value="gym", label="🏟️ Зал", sort_order=2),
                    CustomQuestionOption(value="both", label="🔁 Дом/Зал", sort_order=3),
                ],
                is_required=True,
            ),
        ]

    def custom_questions(self, base_order: int = 11) -> list[CustomQuestion]:
        time_options = [
            ("morning", "🌅 Утро"),
            ("afternoon", "🌞 День"),
            ("evening", "🌇 Вечер"),
            ("any", "🔁 Не важно"),
        ]
        diet_options = [
            ("regular", "🍽️ Обычное"),
            ("vegetarian", "🥗 Вегетарианство"),
            ("vegan", "🌱 Веганство"),
            ("keto", "🥩 Кето"),
            ("intermittent_fasting", "⏳ Интервальное голодание"),
        ]
        time_opts = [
            CustomQuestionOption(value=value, label=label, sort_order=idx)
            for idx, (value, label) in enumerate(time_options, start=1)
        ]
        diet_opts = [
            CustomQuestionOption(value=value, label=label, sort_order=idx)
            for idx, (value, label) in enumerate(diet_options, start=1)
        ]
        return [
                CustomQuestion(
                    key="custom:body_fat_percentage",
                    order=base_order + 0,
                    text="Процент жира (опционально):",
                    answer_type=AnswerType.NUMBER,
                    min_value=5,
                    max_value=60,
                    is_required=False,
                    category="health_info",
                ),
                CustomQuestion(
                    key="custom:sleep_hours",
                    order=base_order + 1,
                    text="Сон в часах:",
                    answer_type=AnswerType.NUMBER,
                    min_value=4,
                    max_value=12,
                    is_required=False,
                    category="lifestyle",
                ),
                CustomQuestion(
                    key="custom:stress_level",
                    order=base_order + 2,
                    text="Уровень стресса (1-10):",
                    answer_type=AnswerType.NUMBER,
                    min_value=1,
                    max_value=10,
                    is_required=False,
                    category="lifestyle",
                ),
                CustomQuestion(
                    key="custom:injuries",
                    order=base_order + 3,
                    text="Есть травмы/ограничения? Опишите кратко.",
                    answer_type=AnswerType.TEXT,
                    is_required=False,
                    category="health_info",
                    tags=["injury"],
                ),
                CustomQuestion(
                    key="custom:preferred_time",
                    order=base_order + 4,
                    text="Предпочитаемое время тренировок:",
                    answer_type=AnswerType.SINGLE_CHOICE,
                    options=time_opts,
                    is_required=False,
                    category="training_customization",
                ),
                CustomQuestion(
                    key="custom:disliked_exercises",
                    order=base_order + 5,
                    text="Есть упражнения, которые нужно исключить?",
                    answer_type=AnswerType.TEXT,
                    is_required=False,
                    category="training_customization",
                ),
                CustomQuestion(
                    key="custom:diet_type",
                    order=base_order + 6,
                    text="Тип питания:",
                    answer_type=AnswerType.SINGLE_CHOICE,
                    options=diet_opts,
                    is_required=False,
                    category="lifestyle",
                ),
                CustomQuestion(
                    key="custom:food_allergies",
                    order=base_order + 7,
                    text="Есть пищевые аллергии? Опишите.",
                    answer_type=AnswerType.TEXT,
                    is_required=False,
                    category="health_info",
                ),
                CustomQuestion(
                    key="custom:water_per_day",
                    order=base_order + 8,
                    text="Сколько воды пьете в день (литры)?",
                    answer_type=AnswerType.NUMBER,
                    min_value=1,
                    max_value=5,
                    is_required=False,
                    category="lifestyle",
                ),
        ]


class CustomQuestionSeeder:
    def __init__(
        self,
        uow: UnitOfWork,
        catalog: CustomQuestionSeedCatalog | None = None,
    ) -> None:
        self._uow = uow
        self._catalog = catalog or CustomQuestionSeedCatalog()

    async def run(self) -> int:
        async with self._uow:
            added = 0
            added += await self._ensure_questions(self._catalog.system_questions())

            existing_questions = await self._uow.custom_questions.list_active_ordered()
            if not any(q.key.startswith("custom:") for q in existing_questions):
                for question in self._catalog.custom_questions():
                    await self._uow.custom_questions.add(question)
                    added += 1

            if added:
                await self._uow.commit()
            return added

    async def _ensure_questions(self, questions: list[CustomQuestion]) -> int:
        added = 0
        for question in questions:
            existing = await self._uow.custom_questions.get_by_key(question.key)
            if existing is None:
                await self._uow.custom_questions.add(question)
                added += 1
        return added

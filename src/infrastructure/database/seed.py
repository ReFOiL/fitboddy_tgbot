from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.application.use_cases.workout_generator.seed_templates import get_default_templates
from src.domain.entities.associations import WorkoutExercise
from src.domain.entities.contraindication import Contraindication
from src.domain.entities.exercise import Exercise
from src.domain.entities.muscle import Muscle
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption
from src.domain.value_objects.questionnaire import AnswerType
from src.domain.entities.workout import WorkoutDifficulty, WorkoutTemplate


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


class WorkoutMvpFixturesSeeder:
    """
    Фикстуры для MVP тренировок:
    - базовые упражнения (10 шт)
    - 3-5 шаблонов тренировок
    - связи WorkoutExercise с параметрами
    - video_url как object_name (ключ) для MinIO (заглушки)
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def run(self) -> int:
        created = 0
        async with self._uow:
            created += await self._seed_muscles_and_contraindications()
            created += await self._seed_exercises()
            created += await self._seed_templates_with_links()
            if created:
                await self._uow.commit()
        return created

    # Каталог упражнений: имя, описание, video_url, список имён мышц, equipment, difficulty, is_cardio, противопоказания
    _EXERCISE_CATALOG: list[tuple[str, str, str, list[str], str, int, bool, list[str]]] = [
        ("Присед", "Базовое упражнение на ноги и корпус.", "videos/demo/squat.mp4", ["quadriceps", "glutes", "core"], "none", 2, False, []),
        ("Жим лежа", "Базовое упражнение на грудь и трицепс.", "videos/demo/bench_press.mp4", ["chest", "triceps", "shoulders"], "barbell", 3, False, []),
        ("Тяга (становая)", "Базовое упражнение на заднюю цепь.", "videos/demo/deadlift.mp4", ["back", "glutes", "hamstrings"], "barbell", 4, False, []),
        ("Жим над головой", "Плечи и трицепс.", "videos/demo/overhead_press.mp4", ["shoulders", "triceps"], "dumbbells", 3, False, []),
        ("Подтягивания", "Спина и бицепс (можно с резинкой).", "videos/demo/pullups.mp4", ["back", "biceps"], "none", 4, False, []),
        ("Тяга гантели в наклоне", "Спина и задняя дельта.", "videos/demo/dumbbell_row.mp4", ["back", "rear_delts", "biceps"], "dumbbells", 2, False, []),
        ("Выпады", "Ноги и ягодицы.", "videos/demo/lunges.mp4", ["quadriceps", "glutes", "hamstrings"], "none", 2, False, []),
        ("Планка", "Статика на корпус.", "videos/demo/plank.mp4", ["core"], "none", 1, False, []),
        ("Берпи", "Кардио + все тело.", "videos/demo/burpees.mp4", ["full_body"], "none", 3, True, []),
        ("Прыжки Jumping Jacks", "Легкое кардио-разогрев.", "videos/demo/jumping_jacks.mp4", ["full_body"], "none", 1, True, []),
    ]

    async def _get_or_create_muscle(self, name: str) -> Muscle:
        m = await self._uow.muscles.get_by_name(name)
        if m is not None:
            return m
        muscle = Muscle(name=name, sort_order=0)
        await self._uow.muscles.add(muscle)
        await self._uow.flush()
        return muscle

    async def _get_or_create_contraindication(self, name: str) -> Contraindication:
        c = await self._uow.contraindications.get_by_name(name)
        if c is not None:
            return c
        contra = Contraindication(name=name, sort_order=0)
        await self._uow.contraindications.add(contra)
        await self._uow.flush()
        return contra

    async def _seed_muscles_and_contraindications(self) -> int:
        added = 0
        muscle_names: set[str] = set()
        contra_names: set[str] = set()
        for _, _, _, muscles, _, _, _, contras in self._EXERCISE_CATALOG:
            muscle_names.update(muscles)
            contra_names.update(contras)
        for name in muscle_names:
            existing = await self._uow.muscles.get_by_name(name)
            if existing is None:
                await self._uow.muscles.add(Muscle(name=name, sort_order=0))
                await self._uow.flush()
                added += 1
        for name in contra_names:
            existing = await self._uow.contraindications.get_by_name(name)
            if existing is None:
                await self._uow.contraindications.add(Contraindication(name=name, sort_order=0))
                await self._uow.flush()
                added += 1
        return added

    async def _seed_exercises(self) -> int:
        added = 0
        for name, description, video_url, muscle_names, equipment, difficulty, is_cardio, contra_names in self._EXERCISE_CATALOG:
            existing = await self._uow.exercises.get_by_name(name)
            if existing is not None:
                continue
            muscles = [await self._get_or_create_muscle(n) for n in muscle_names]
            contras = [await self._get_or_create_contraindication(n) for n in contra_names]
            exercise = Exercise(
                name=name,
                description=description,
                video_url=video_url,
                equipment=equipment,
                difficulty=difficulty,
                is_cardio=is_cardio,
            )
            exercise.muscles = muscles
            exercise.contraindications = contras
            await self._uow.exercises.add(exercise)
            await self._uow.flush()
            added += 1
        return added

    async def _seed_templates_with_links(self) -> int:
        existing_templates = await self._uow.workouts.list_all()
        by_title = {t.title: t for t in existing_templates}

        exercises = await self._uow.exercises.list_all()
        ex_by_name = {e.name: e for e in exercises}

        def ex(name: str) -> Exercise:
            return ex_by_name[name]

        templates: list[WorkoutTemplate] = [
            WorkoutTemplate(
                title="Силовая — Full Body (новичок)",
                goal="muscle_gain",
                difficulty=WorkoutDifficulty.LOW,
                equipment="dumbbells",
                days_per_week=3,
                description="Базовая силовая на все тело.",
                is_active=True,
                workout_exercises=[
                    WorkoutExercise(exercise=ex("Присед"), sort_order=1, sets=3, reps=10, rest_seconds=60),
                    WorkoutExercise(exercise=ex("Жим над головой"), sort_order=2, sets=3, reps=10, rest_seconds=60),
                    WorkoutExercise(exercise=ex("Тяга гантели в наклоне"), sort_order=3, sets=3, reps=12, rest_seconds=60),
                    WorkoutExercise(exercise=ex("Планка"), sort_order=4, duration_seconds=45, rest_seconds=45),
                ],
            ),
            WorkoutTemplate(
                title="Похудение — Кардио круговая (дом)",
                goal="weight_loss",
                difficulty=WorkoutDifficulty.LOW,
                equipment="none",
                days_per_week=3,
                description="Короткие круги + базовые движения.",
                is_active=True,
                workout_exercises=[
                    WorkoutExercise(exercise=ex("Прыжки Jumping Jacks"), sort_order=1, duration_seconds=45, rest_seconds=20),
                    WorkoutExercise(exercise=ex("Берпи"), sort_order=2, sets=3, reps=10, rest_seconds=60),
                    WorkoutExercise(exercise=ex("Выпады"), sort_order=3, sets=3, reps=12, rest_seconds=60),
                    WorkoutExercise(exercise=ex("Планка"), sort_order=4, duration_seconds=45, rest_seconds=45),
                ],
            ),
            WorkoutTemplate(
                title="Силовая — База со штангой",
                goal="muscle_gain",
                difficulty=WorkoutDifficulty.MEDIUM,
                equipment="barbell",
                days_per_week=3,
                description="База: присед/жим/становая.",
                is_active=True,
                workout_exercises=[
                    WorkoutExercise(exercise=ex("Присед"), sort_order=1, sets=5, reps=5, rest_seconds=120),
                    WorkoutExercise(exercise=ex("Жим лежа"), sort_order=2, sets=5, reps=5, rest_seconds=120),
                    WorkoutExercise(exercise=ex("Тяга (становая)"), sort_order=3, sets=3, reps=5, rest_seconds=180),
                ],
            ),
            WorkoutTemplate(
                title="Выносливость — базовая",
                goal="endurance",
                difficulty=WorkoutDifficulty.MEDIUM,
                equipment="none",
                days_per_week=4,
                description="Кардио+корпус.",
                is_active=True,
                workout_exercises=[
                    WorkoutExercise(exercise=ex("Прыжки Jumping Jacks"), sort_order=1, duration_seconds=60, rest_seconds=20),
                    WorkoutExercise(exercise=ex("Берпи"), sort_order=2, sets=4, reps=8, rest_seconds=60),
                    WorkoutExercise(exercise=ex("Планка"), sort_order=3, duration_seconds=60, rest_seconds=30),
                ],
            ),
        ]

        added = 0
        for tpl in templates:
            if tpl.title in by_title:
                continue
            await self._uow.workouts.add(tpl)
            added += 1
        return added


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

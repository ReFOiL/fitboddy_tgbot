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
            templates_data = get_default_templates()
            
            # Устанавливаем связи required_equipment на основе имени оборудования
            for template, equipment_name in templates_data:
                if equipment_name:
                    # Ищем Equipment по name
                    equipment = await self._uow.equipment.get_by_name(equipment_name)
                    if equipment:
                        template.required_equipment.append(equipment)
                
                await self._uow.workouts.add(template)
            await self._uow.commit()
            return len(templates_data)


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

        templates_data: list[tuple[WorkoutTemplate, str | None]] = [
            (
                WorkoutTemplate(
                    title="Силовая — Full Body (новичок)",
                    goal="muscle_gain",
                    difficulty=WorkoutDifficulty.LOW,
                    days_per_week=3,
                    description="Базовая силовая на все тело.",
                    is_active=True,
                    intensity_factor=1.0,
                    workout_category="full_body",
                    workout_exercises=[
                        WorkoutExercise(exercise=ex("Присед"), sort_order=1, sets=3, reps=10, rest_seconds=60),
                        WorkoutExercise(exercise=ex("Жим над головой"), sort_order=2, sets=3, reps=10, rest_seconds=60),
                        WorkoutExercise(exercise=ex("Тяга гантели в наклоне"), sort_order=3, sets=3, reps=12, rest_seconds=60),
                        WorkoutExercise(exercise=ex("Планка"), sort_order=4, duration_seconds=45, rest_seconds=45),
                    ],
                ),
                "dumbbells",
            ),
            (
                WorkoutTemplate(
                    title="Похудение — Кардио круговая (дом)",
                    goal="weight_loss",
                    difficulty=WorkoutDifficulty.LOW,
                    days_per_week=3,
                    description="Короткие круги + базовые движения.",
                    is_active=True,
                    intensity_factor=0.8,
                    workout_category="cardio",
                    workout_exercises=[
                        WorkoutExercise(exercise=ex("Прыжки Jumping Jacks"), sort_order=1, duration_seconds=45, rest_seconds=20),
                        WorkoutExercise(exercise=ex("Берпи"), sort_order=2, sets=3, reps=10, rest_seconds=60),
                        WorkoutExercise(exercise=ex("Выпады"), sort_order=3, sets=3, reps=12, rest_seconds=60),
                        WorkoutExercise(exercise=ex("Планка"), sort_order=4, duration_seconds=45, rest_seconds=45),
                    ],
                ),
                None,  # Без оборудования
            ),
            (
                WorkoutTemplate(
                    title="Силовая — База со штангой",
                    goal="muscle_gain",
                    difficulty=WorkoutDifficulty.MEDIUM,
                    days_per_week=3,
                    description="База: присед/жим/становая.",
                    is_active=True,
                    intensity_factor=1.5,
                    workout_category="full_body",
                    workout_exercises=[
                        WorkoutExercise(exercise=ex("Присед"), sort_order=1, sets=5, reps=5, rest_seconds=120),
                        WorkoutExercise(exercise=ex("Жим лежа"), sort_order=2, sets=5, reps=5, rest_seconds=120),
                        WorkoutExercise(exercise=ex("Тяга (становая)"), sort_order=3, sets=3, reps=5, rest_seconds=180),
                    ],
                ),
                "barbell",
            ),
            (
                WorkoutTemplate(
                    title="Выносливость — базовая",
                    goal="endurance",
                    difficulty=WorkoutDifficulty.MEDIUM,
                    days_per_week=4,
                    description="Кардио+корпус.",
                    is_active=True,
                    intensity_factor=1.2,
                    workout_category="cardio",
                    workout_exercises=[
                        WorkoutExercise(exercise=ex("Прыжки Jumping Jacks"), sort_order=1, duration_seconds=60, rest_seconds=20),
                        WorkoutExercise(exercise=ex("Берпи"), sort_order=2, sets=4, reps=8, rest_seconds=60),
                        WorkoutExercise(exercise=ex("Планка"), sort_order=3, duration_seconds=60, rest_seconds=30),
                    ],
                ),
                None,  # Без оборудования
            ),
        ]

        added = 0
        for tpl, equipment_name in templates_data:
            if tpl.title in by_title:
                continue
            
            # Устанавливаем связи required_equipment на основе имени оборудования
            if equipment_name:
                equipment = await self._uow.equipment.get_by_name(equipment_name)
                if equipment:
                    tpl.required_equipment.append(equipment)
            
            await self._uow.workouts.add(tpl)
            added += 1
        return added


class CustomQuestionSeedCatalog:
    """Системные вопросы MVP + один пример кастомного (травмы/ограничения)."""

    def system_questions(self) -> list[CustomQuestion]:
        return [
            CustomQuestion(
                is_system=True,
                key="system:goal",
                order=1,
                text="Какая у вас основная цель тренировок?",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="weight_loss", label="Похудение", sort_order=1),
                    CustomQuestionOption(value="muscle_gain", label="Набор мышечной массы", sort_order=2),
                    CustomQuestionOption(value="endurance", label="Повышение выносливости", sort_order=3),
                    CustomQuestionOption(value="maintenance", label="Поддержание формы", sort_order=4),
                    CustomQuestionOption(value="rehabilitation", label="Реабилитация", sort_order=5),
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
                key="system:workout_location",
                order=3,
                text="Где вы планируете тренироваться?",
                answer_type=AnswerType.SINGLE_CHOICE,
                options=[
                    CustomQuestionOption(value="home", label="Дома", sort_order=1),
                    CustomQuestionOption(value="gym", label="В фитнес-зале", sort_order=2),
                    CustomQuestionOption(value="both", label="И дома, и в зале", sort_order=3),
                ],
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key="system:equipment",
                order=4,
                text="Какое оборудование у вас есть?",
                answer_type=AnswerType.MULTIPLE_CHOICE,
                options=[
                    CustomQuestionOption(value="dumbbells", label="Гантели", sort_order=1),
                    CustomQuestionOption(value="barbell", label="Штанга", sort_order=2),
                    CustomQuestionOption(value="resistance_bands", label="Резинки / эспандеры", sort_order=3),
                    CustomQuestionOption(value="kettlebell", label="Гиря", sort_order=4),
                    CustomQuestionOption(value="treadmill", label="Беговая дорожка", sort_order=5),
                    CustomQuestionOption(value="other", label="Другое", sort_order=6),
                    CustomQuestionOption(value="none", label="Нет оборудования", sort_order=7),
                ],
                is_required=True,
            ),
            CustomQuestion(
                is_system=True,
                key="system:workouts_per_week",
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
            changes = 0
            changes += await self._ensure_questions(self._catalog.system_questions())
            changes += await self._ensure_mvp_custom_question()
            if changes:
                await self._uow.commit()
            return changes

    async def _ensure_questions(self, questions: list[CustomQuestion]) -> int:
        added = 0
        for question in questions:
            existing = await self._uow.custom_questions.get_by_key(question.key)
            if existing is None:
                await self._uow.custom_questions.add(question)
                added += 1
        return added

    async def _ensure_mvp_custom_question(self) -> int:
        if await self._uow.custom_questions.get_by_key("custom:health_notes") is not None:
            return 0
        await self._uow.custom_questions.add(self._catalog.mvp_custom_question())
        return 1

from __future__ import annotations

from src.application.interfaces.repositories import UnitOfWork
from src.domain.entities.contraindication import Contraindication
from src.domain.entities.exercise import Exercise
from src.domain.entities.muscle import Muscle
from src.domain.entities.questionnaire import CustomQuestion, CustomQuestionOption
from src.domain.value_objects.questionnaire import AnswerType


class WorkoutMvpFixturesSeeder:
    """
    Фикстуры для MVP тренировок:
    - каталог из 60 упражнений (категории для планировщика; много вариантов без инвентаря)
    - video_url как ключ для MinIO (заглушки)
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def run(self) -> int:
        created = 0
        async with self._uow:
            created += await self._seed_muscles_and_contraindications()
            created += await self._seed_exercises()
            if created:
                await self._uow.commit()
        return created

    # name, description, video_url, muscles, equipment, difficulty, is_cardio, contras, workout_category
    _EXERCISE_CATALOG: list[tuple[str, str, str, list[str], str, int, bool, list[str], str]] = [
        ("Присед", "Базовое упражнение на ноги и корпус.", "videos/demo/squat.mp4", ["quadriceps", "glutes", "core"], "none", 2, False, [], "lower"),
        ("Жим лежа", "Базовое упражнение на грудь и трицепс.", "videos/demo/bench_press.mp4", ["chest", "triceps", "shoulders"], "barbell", 3, False, [], "upper"),
        ("Тяга (становая)", "Базовое упражнение на заднюю цепь.", "videos/demo/deadlift.mp4", ["back", "glutes", "hamstrings"], "barbell", 4, False, [], "lower"),
        ("Жим над головой", "Плечи и трицепс.", "videos/demo/overhead_press.mp4", ["shoulders", "triceps"], "dumbbells", 3, False, [], "upper"),
        ("Подтягивания", "Спина и бицепс (можно с резинкой).", "videos/demo/pullups.mp4", ["back", "biceps"], "none", 4, False, [], "upper"),
        ("Тяга гантели в наклоне", "Спина и задняя дельта.", "videos/demo/dumbbell_row.mp4", ["back", "rear_delts", "biceps"], "dumbbells", 2, False, [], "upper"),
        ("Выпады", "Ноги и ягодицы.", "videos/demo/lunges.mp4", ["quadriceps", "glutes", "hamstrings"], "none", 2, False, [], "lower"),
        ("Планка", "Статика на корпус.", "videos/demo/plank.mp4", ["core"], "none", 1, False, [], "full_body"),
        ("Берпи", "Кардио + все тело.", "videos/demo/burpees.mp4", ["full_body"], "none", 3, True, [], "cardio"),
        ("Прыжки Jumping Jacks", "Легкое кардио-разогрев.", "videos/demo/jumping_jacks.mp4", ["full_body"], "none", 1, True, [], "cardio"),
        ("Отжимания от пола", "Грудь и трицепс без веса.", "videos/demo/pushups.mp4", ["chest", "triceps", "core"], "none", 2, False, [], "upper"),
        ("Румынская тяга", "Задняя цепь с гантелями.", "videos/demo/rdl.mp4", ["hamstrings", "glutes", "back"], "dumbbells", 3, False, [], "lower"),
        ("Французский жим", "Изоляция трицепса.", "videos/demo/french_press.mp4", ["triceps"], "dumbbells", 2, False, [], "upper"),
        ("Гоблет-присед", "Присед с удержанием веса.", "videos/demo/goblet_squat.mp4", ["quadriceps", "glutes", "core"], "dumbbells", 2, False, [], "lower"),
        ("Скалолаз", "Кардио на корпус и ноги.", "videos/demo/mountain_climber.mp4", ["core", "full_body"], "none", 2, True, [], "cardio"),
        ("Супермен", "Разгибание спины лёжа.", "videos/demo/superman.mp4", ["back", "glutes"], "none", 1, False, [], "full_body"),
        ("Шаги на месте", "Лёгкое кардио.", "videos/demo/march.mp4", ["quadriceps", "full_body"], "none", 1, True, [], "cardio"),
        ("Обратные отжимания", "Трицепс от скамьи/края.", "videos/demo/bench_dips.mp4", ["triceps", "shoulders"], "none", 3, False, [], "upper"),
        ("Боковая планка", "Статика косых.", "videos/demo/side_plank.mp4", ["core"], "none", 2, False, [], "full_body"),
        ("Велосипед", "Кручение локтей к колену лёжа.", "videos/demo/bicycle_crunch.mp4", ["core"], "none", 2, False, [], "full_body"),
        ("Высокие колени", "Подъём коленей к груди стоя.", "videos/demo/high_knees.mp4", ["core", "hip_flexors", "full_body"], "none", 1, True, [], "cardio"),
        ("Отжимания широкие", "Акцент на грудь.", "videos/demo/pushups_wide.mp4", ["chest", "shoulders"], "none", 2, False, [], "upper"),
        ("Отжимания узкие", "Акцент на трицепс.", "videos/demo/pushups_narrow.mp4", ["triceps", "chest", "core"], "none", 2, False, [], "upper"),
        ("Ягодичный мост", "Сжатие ягодиц лёжа на спине.", "videos/demo/hip_bridge.mp4", ["glutes", "hamstrings", "core"], "none", 1, False, [], "lower"),
        ("Присед у стены", "Статика квадрицепсов у стены.", "videos/demo/wall_squat.mp4", ["quadriceps", "glutes"], "none", 2, False, [], "lower"),
        ("Выпад в сторону", "Боковой выпад без веса.", "videos/demo/side_lunge.mp4", ["quadriceps", "glutes", "adductors"], "none", 2, False, [], "lower"),
        ("Наклон вперёд без веса", "Мягкая проработка задней цепи.", "videos/demo/bodyweight_good_morning.mp4", ["hamstrings", "back", "glutes"], "none", 1, False, [], "full_body"),
        ("Альпинист в упоре", "Усложнённый темп скалолаза.", "videos/demo/mountain_climber_slow.mp4", ["core", "shoulders", "full_body"], "none", 2, True, [], "cardio"),
        ("Присед сумо", "Широкая постановка стоп.", "videos/demo/sumo_squat.mp4", ["quadriceps", "glutes", "adductors"], "none", 2, False, [], "lower"),
        ("Отжимания от стены", "Лёгкий вариант отжиманий.", "videos/demo/wall_pushup.mp4", ["chest", "shoulders", "triceps"], "none", 1, False, [], "upper"),
        ("Обратная планка", "Упор сзади на ладони и пятки.", "videos/demo/reverse_plank.mp4", ["shoulders", "back", "core", "glutes"], "none", 2, False, [], "full_body"),
        ("Полый корпус", "Hollow body: лопатки и ноги от пола.", "videos/demo/hollow_hold.mp4", ["core"], "none", 2, False, [], "full_body"),
        ("Подъём ног лёжа", "Пресс и сгибатели бедра.", "videos/demo/lying_leg_raise.mp4", ["core", "hip_flexors"], "none", 2, False, [], "full_body"),
        ("Русское скручивание", "Повороты корпуса без веса.", "videos/demo/russian_twist.mp4", ["obliques", "core"], "none", 1, False, [], "full_body"),
        ("Выпады вперёд ходьбой", "Чередование ног в движении.", "videos/demo/walking_lunge.mp4", ["quadriceps", "glutes", "hamstrings"], "none", 2, False, [], "lower"),
        ("Присед на одной ноге с опорой", "Упрощённый пистолет у стены/стула.", "videos/demo/assisted_pistol.mp4", ["quadriceps", "glutes", "core"], "none", 3, False, [], "lower"),
        ("Плиометрический выпад", "Выпад со сменой ног в прыжке.", "videos/demo/jumping_lunge.mp4", ["quadriceps", "glutes", "full_body"], "none", 3, True, [], "cardio"),
        ("Имитация скакалки", "Прыжки на носках без каната.", "videos/demo/shadow_jump_rope.mp4", ["calves", "shoulders", "full_body"], "none", 1, True, [], "cardio"),
        ("Ползун медведя", "На четвереньках вперёд-назад.", "videos/demo/bear_crawl.mp4", ["full_body", "core", "shoulders"], "none", 2, True, [], "full_body"),
        ("Ход краба", "Садясь, движение спиной вперёд.", "videos/demo/crab_walk.mp4", ["triceps", "shoulders", "glutes"], "none", 2, False, [], "upper"),
        ("Инчворм", "Из стоя в планку шагами рук.", "videos/demo/inchworm.mp4", ["hamstrings", "core", "shoulders"], "none", 2, False, [], "full_body"),
        ("Складка стоя — планка", "Динамическая связка.", "videos/demo/walkout_plank.mp4", ["core", "shoulders", "hamstrings"], "none", 2, False, [], "full_body"),
        ("Тяга локтя в планке", "Подтягивание локтя к ребру.", "videos/demo/renegade_row_bodyweight.mp4", ["back", "core", "biceps"], "none", 2, False, [], "upper"),
        ("Разведение рук в Т", "Наклон, махи назад без веса.", "videos/demo/bodyweight_rear_fly.mp4", ["rear_delts", "back"], "none", 1, False, [], "upper"),
        ("Круги руками", "Разминка плеч.", "videos/demo/arm_circles.mp4", ["shoulders"], "none", 1, False, [], "upper"),
        ("Присед с паузой", "Задержка в нижней точке.", "videos/demo/pause_squat.mp4", ["quadriceps", "glutes", "core"], "none", 2, False, [], "lower"),
        ("Попеременные колени", "По одному колену к груди стоя.", "videos/demo/alternating_knee_drive.mp4", ["hip_flexors", "core", "full_body"], "none", 1, True, [], "cardio"),
        ("Скалолаз к локтю", "Колено к противоположному локтю.", "videos/demo/cross_body_mountain_climber.mp4", ["core", "obliques"], "none", 2, True, [], "cardio"),
        ("Боковой шаг", "Низкие шаги в сторону.", "videos/demo/side_shuffle.mp4", ["quadriceps", "glutes", "calves"], "none", 1, True, [], "cardio"),
        ("Звёздный прыжок", "Прыжок «звезда».", "videos/demo/star_jump.mp4", ["full_body"], "none", 2, True, [], "cardio"),
        ("Отжимания с колен", "Упрощённые отжимания.", "videos/demo/knee_pushup.mp4", ["chest", "triceps"], "none", 1, False, [], "upper"),
        ("Дипы на трицепс с пола", "Разгибание из упора лёжа.", "videos/demo/tricep_pushup_floor.mp4", ["triceps", "chest"], "none", 2, False, [], "upper"),
        ("Ягодичный мост одной ногой", "Мост с вытянутой ногой.", "videos/demo/single_leg_bridge.mp4", ["glutes", "hamstrings", "core"], "none", 2, False, [], "lower"),
        ("Подъём на носки стоя", "Икры без веса.", "videos/demo/calf_raise.mp4", ["calves"], "none", 1, False, [], "lower"),
        ("Скручивание лёжа", "Классический подъём корпуса.", "videos/demo/crunch.mp4", ["core"], "none", 1, False, [], "full_body"),
        ("Подъём таза лёжа", "Мост с акцентом на ягодицы.", "videos/demo/hip_thrust_floor.mp4", ["glutes", "core"], "none", 1, False, [], "lower"),
        ("Отведение ноги назад стоя", "Ягодица без веса.", "videos/demo/kickback_glute.mp4", ["glutes", "back"], "none", 1, False, [], "lower"),
        ("Шраги без веса", "Сжатие плеч к ушам.", "videos/demo/bodyweight_shrug.mp4", ["traps", "shoulders"], "none", 1, False, [], "upper"),
        ("Мёртвый жук", "Разгибание противоположных конечностей.", "videos/demo/dead_bug.mp4", ["core", "hip_flexors"], "none", 1, False, [], "full_body"),
        ("Планка с касанием плеч", "Перенос веса на одну руку.", "videos/demo/plank_shoulder_tap.mp4", ["core", "shoulders"], "none", 2, False, [], "full_body"),
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
        for row in self._EXERCISE_CATALOG:
            _, _, _, muscles, _, _, _, contras, _ = row
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
        for (
            name,
            description,
            video_url,
            muscle_names,
            equipment,
            difficulty,
            is_cardio,
            contra_names,
            workout_category,
        ) in self._EXERCISE_CATALOG:
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
                workout_category=workout_category,
            )
            exercise.muscles = muscles
            exercise.contraindications = contras
            await self._uow.exercises.add(exercise)
            await self._uow.flush()
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

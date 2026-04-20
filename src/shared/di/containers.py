from dependency_injector import containers, providers
from aiogram import Bot
from redis.asyncio import Redis

from src.application.services.custom_question_admin import CustomQuestionAdminService
from src.application.services.admin_users import AdminUserService
from src.application.services.exercise_admin import ExerciseAdminService
from src.application.services.muscle_admin import MuscleAdminService
from src.application.services.contraindication_admin import ContraindicationAdminService
from src.application.services.equipment_admin import EquipmentAdminService
from src.application.services.notification import NotificationService
from src.application.services.profile_completion import ProfileCompletionService
from src.application.services.questionnaire import QuestionnaireService
from src.application.factories.answer_builder_factory import AnswerBuilderFactory
from src.application.services.questionnaire_answers import QuestionnaireAnswerService
from src.application.services.questionnaire_flow_queries import QuestionnaireFlowQueries
from src.application.services.user_registration import UserRegistrationService
from src.commons.validators import (
    BoolValidator,
    IntValidator,
    MultiChoiceValidator,
    SingleChoiceValidator,
    TextValidator,
)
from src.domain.questionnaire import (
    AnswerTypeRegistry,
    AnswerValidationPipeline,
    AnswerValidator,
    BooleanAnswerStrategy,
    MultiChoiceAnswerStrategy,
    NumberAnswerStrategy,
    OptionalSkipStep,
    QuestionFactory,
    RequiredAnswerStep,
    SingleChoiceAnswerStrategy,
    TextAnswerStrategy,
)
from src.domain.value_objects.questionnaire import AnswerType
from src.application.services.subscription import PremiumAccess, SubscriptionService
from src.application.use_cases.payment.cryptobot import CryptoBotPaymentUseCase
from src.application.use_cases.workout.query import (
    CompleteTodayWorkoutUseCase,
    GetExerciseDetailUseCase,
    GetMyPlanUseCase,
    GetTodayWorkoutUseCase,
)
from src.application.workout.scheduler.service import WorkoutScheduler
from src.application.workout.scheduler.policies import (
    RecoveryOverlapScorer,
    RecoveryPenaltyPolicy,
    RecoveryWindowPolicy,
    WeeklyPatternPolicy,
)
from src.application.workout.scheduler.strategies import (
    AnchorSelectionStrategy,
    SessionCompositionStrategy,
)
from src.application.workout.planning import (
    LoadScalingPolicy,
    PlanVariationSeedFactory,
    PlanningContextFactory,
)
from src.application.workout.plan_management import ActivePlanPolicy, UserPlanOrchestrator
from src.application.services.training_plan_generator import TrainingPlanGenerator
from src.application.services.user_plan_service import UserPlanService
from src.application.services.training_plan_admin import TrainingPlanAdminService
from src.presentation.telegram_bot.flows.questionnaire.flow_service import QuestionnaireFlow
from src.presentation.telegram_bot.flows.questionnaire.presenter import QuestionnairePresenter
from src.presentation.telegram_bot.flows.workouts.flow_service import WorkoutsFlow
from src.presentation.web_admin.question_controller import QuestionController
from src.presentation.web_admin.question_presenters import (
    OptionsNormalizer,
    QuestionPayloadBuilder,
    QuestionPresenter,
)
from src.presentation.web_admin.user_controller import UserController
from src.presentation.web_admin.user_presenters import UserPresenter
from src.presentation.web_admin.exercise_controller import ExerciseController
from src.presentation.web_admin.muscle_controller import MuscleController
from src.presentation.web_admin.contraindication_controller import ContraindicationController
from src.presentation.web_admin.equipment_controller import EquipmentController
from src.presentation.web_admin.training_plan_admin_controller import TrainingPlanAdminController
from src.infrastructure.cache.redis_repository import RedisCache
from src.infrastructure.database.session import create_engine, create_session_factory
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.external.cryptobot.client import CryptoBotClient
from src.infrastructure.external.file_storage import VideoFileStorage
from src.infrastructure.external.minio_client import MinioClient
from src.infrastructure.external.s3_storage.minio_client import MinioStorage
from src.infrastructure.external.telegram.bot_client import TelegramNotifier
from src.shared.config.settings import get_settings


class Container(containers.DeclarativeContainer):
    user_registration_service: providers.Provider[UserRegistrationService]
    profile_completion_service: providers.Provider[ProfileCompletionService]
    questionnaire_answer_service: providers.Provider[QuestionnaireAnswerService]
    questionnaire_flow_queries: providers.Provider[QuestionnaireFlowQueries]
    questionnaire_flow: providers.Provider[QuestionnaireFlow]
    workouts_flow: providers.Provider[WorkoutsFlow]
    user_controller: providers.Provider[UserController]
    premium_access: providers.Provider[PremiumAccess]
    wiring_config = containers.WiringConfiguration(
        packages=["src.presentation.telegram_bot.handlers", "src.presentation.web_admin"]
    )

    settings = providers.Singleton(get_settings)

    engine = providers.Singleton(create_engine, database_url=settings.provided.database.url)
    session_factory = providers.Singleton(create_session_factory, engine=engine)
    uow = providers.Factory(SQLAlchemyUnitOfWork, session_factory=session_factory)

    bot = providers.Singleton(Bot, token=settings.provided.bot.token)
    redis = providers.Singleton(Redis.from_url, url=settings.provided.redis.url)
    cache = providers.Factory(RedisCache, client=redis)

    cryptobot_client = providers.Singleton(
        CryptoBotClient,
        api_token=settings.provided.cryptobot.api_token,
        webhook_secret=settings.provided.cryptobot.webhook_secret,
    )
    minio_storage = providers.Singleton(
        MinioStorage,
        endpoint=settings.provided.minio.endpoint,
        access_key=settings.provided.minio.access_key,
        secret_key=settings.provided.minio.secret_key,
        secure=settings.provided.minio.secure,
    )
    minio_client = providers.Singleton(
        MinioClient,
        endpoint=settings.provided.minio.endpoint,
        access_key=settings.provided.minio.access_key,
        secret_key=settings.provided.minio.secret_key,
        secure=settings.provided.minio.secure,
        presigned_endpoint=settings.provided.minio.public_endpoint,
    )
    video_file_storage = providers.Singleton(
        VideoFileStorage,
        client=minio_client,
        bucket=settings.provided.minio.bucket,
    )

    notifier = providers.Factory(TelegramNotifier, bot=bot)
    notification_service = providers.Factory(NotificationService, notifier=notifier)
    subscription_service = providers.Factory(SubscriptionService)
    premium_access = providers.Singleton(PremiumAccess, _settings=settings)

    payment_use_case = providers.Factory(
        CryptoBotPaymentUseCase,
        gateway=cryptobot_client,
        uow=uow,
        subscription_service=subscription_service,
        notification_service=notification_service,
    )

    weekly_pattern_policy = providers.Singleton(WeeklyPatternPolicy)
    recovery_window_policy = providers.Singleton(RecoveryWindowPolicy)
    recovery_penalty_policy = providers.Singleton(RecoveryPenaltyPolicy)
    recovery_overlap_scorer = providers.Singleton(RecoveryOverlapScorer)
    anchor_selection_strategy = providers.Singleton(AnchorSelectionStrategy)
    session_composition_strategy = providers.Singleton(
        SessionCompositionStrategy,
        overlap_scorer=recovery_overlap_scorer,
    )
    workout_scheduler = providers.Singleton(
        WorkoutScheduler,
        weekly_pattern_policy=weekly_pattern_policy,
        anchor_selection_strategy=anchor_selection_strategy,
        recovery_window_policy=recovery_window_policy,
        recovery_penalty_policy=recovery_penalty_policy,
        recovery_overlap_scorer=recovery_overlap_scorer,
        session_composition_strategy=session_composition_strategy,
    )
    plan_variation_seed_factory = providers.Singleton(PlanVariationSeedFactory)
    planning_context_factory = providers.Singleton(
        PlanningContextFactory,
        seed_factory=plan_variation_seed_factory,
    )
    load_scaling_policy = providers.Singleton(LoadScalingPolicy)
    training_plan_generator = providers.Factory(
        TrainingPlanGenerator,
        scheduler=workout_scheduler,
        context_factory=planning_context_factory,
        load_scaling_policy=load_scaling_policy,
    )
    active_plan_policy = providers.Singleton(ActivePlanPolicy)
    user_plan_orchestrator = providers.Factory(
        UserPlanOrchestrator,
        plan_generator=training_plan_generator,
        active_plan_policy=active_plan_policy,
    )
    user_plan_service = providers.Factory(
        UserPlanService,
        uow=uow,
        orchestrator=user_plan_orchestrator,
    )
    get_my_plan_use_case = providers.Factory(
        GetMyPlanUseCase,
        uow=uow,
        user_plan_service=user_plan_service,
    )
    get_today_workout_use_case = providers.Factory(
        GetTodayWorkoutUseCase,
        uow=uow,
        user_plan_service=user_plan_service,
    )
    complete_today_workout_use_case = providers.Factory(
        CompleteTodayWorkoutUseCase,
        uow=uow,
        user_plan_service=user_plan_service,
    )
    get_exercise_detail_use_case = providers.Factory(
        GetExerciseDetailUseCase,
        uow=uow,
    )

    text_validator = providers.Factory(TextValidator)
    int_validator = providers.Factory(IntValidator)
    bool_validator = providers.Factory(BoolValidator)
    single_choice_validator = providers.Factory(SingleChoiceValidator)
    multi_choice_validator = providers.Factory(MultiChoiceValidator)

    required_answer_step = providers.Factory(RequiredAnswerStep)
    optional_skip_step = providers.Factory(OptionalSkipStep)
    answer_validation_pipeline = providers.Factory(
        AnswerValidationPipeline,
        steps=providers.List(required_answer_step, optional_skip_step),
    )

    text_answer_strategy = providers.Factory(TextAnswerStrategy, validator=text_validator)
    number_answer_strategy = providers.Factory(NumberAnswerStrategy, validator=int_validator)
    boolean_answer_strategy = providers.Factory(BooleanAnswerStrategy, validator=bool_validator)
    single_choice_strategy = providers.Factory(
        SingleChoiceAnswerStrategy,
        validator=single_choice_validator,
    )
    multi_choice_strategy = providers.Factory(
        MultiChoiceAnswerStrategy,
        validator=multi_choice_validator,
    )
    answer_type_registry = providers.Factory(
        AnswerTypeRegistry,
        strategies=providers.Dict(
            {
                AnswerType.TEXT: text_answer_strategy,
                AnswerType.NUMBER: number_answer_strategy,
                AnswerType.BOOLEAN: boolean_answer_strategy,
                AnswerType.SINGLE_CHOICE: single_choice_strategy,
                AnswerType.MULTIPLE_CHOICE: multi_choice_strategy,
            }
        ),
    )
    answer_validator = providers.Factory(
        AnswerValidator,
        registry=answer_type_registry,
        pipeline=answer_validation_pipeline,
    )
    question_factory = providers.Factory(QuestionFactory)
    answer_builder_factory = providers.Factory(AnswerBuilderFactory)
    questionnaire_service = providers.Factory(
        QuestionnaireService,
        uow=uow,
        validator=answer_validator,
        factory=question_factory,
        answer_builder_factory=answer_builder_factory,
    )
    questionnaire_flow_queries = providers.Factory(
        QuestionnaireFlowQueries,
        service=questionnaire_service,
    )
    questionnaire_answer_service = providers.Factory(
        QuestionnaireAnswerService,
        service=questionnaire_service,
    )

    user_registration_service = providers.Factory(UserRegistrationService, uow=uow)
    profile_completion_service = providers.Factory(ProfileCompletionService, uow=uow)

    questionnaire_presenter = providers.Factory(QuestionnairePresenter)
    questionnaire_flow = providers.Factory(
        QuestionnaireFlow,
        queries=questionnaire_flow_queries,
        user_service=user_registration_service,
        profile_service=profile_completion_service,
        answer_service=questionnaire_answer_service,
        presenter=questionnaire_presenter,
        user_plan_service=user_plan_service,
    )

    workouts_flow = providers.Factory(WorkoutsFlow, uow=uow)

    custom_question_admin_service = providers.Factory(
        CustomQuestionAdminService,
        uow=uow,
    )

    admin_user_service = providers.Factory(AdminUserService, uow=uow)
    user_presenter = providers.Factory(UserPresenter)
    user_controller = providers.Factory(
        UserController,
        service=admin_user_service,
        presenter=user_presenter,
    )

    options_normalizer = providers.Factory(OptionsNormalizer)
    question_payload_builder = providers.Factory(
        QuestionPayloadBuilder,
        normalizer=options_normalizer,
    )
    question_presenter = providers.Factory(QuestionPresenter)
    question_controller = providers.Factory(
        QuestionController,
        service=custom_question_admin_service,
        builder=question_payload_builder,
        presenter=question_presenter,
    )

    exercise_admin_service = providers.Factory(ExerciseAdminService, uow=uow)
    muscle_admin_service = providers.Factory(MuscleAdminService, uow=uow)
    contraindication_admin_service = providers.Factory(ContraindicationAdminService, uow=uow)
    equipment_admin_service = providers.Factory(EquipmentAdminService, uow=uow)
    exercise_controller = providers.Factory(
        ExerciseController,
        service=exercise_admin_service,
        video_storage=video_file_storage,
    )
    muscle_controller = providers.Factory(
        MuscleController,
        service=muscle_admin_service,
    )
    contraindication_controller = providers.Factory(
        ContraindicationController,
        service=contraindication_admin_service,
    )
    equipment_controller = providers.Factory(
        EquipmentController,
        service=equipment_admin_service,
    )

    training_plan_admin_service = providers.Factory(TrainingPlanAdminService, uow=uow)
    training_plan_admin_controller = providers.Factory(
        TrainingPlanAdminController,
        service=training_plan_admin_service,
    )


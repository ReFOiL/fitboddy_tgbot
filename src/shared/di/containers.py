from dependency_injector import containers, providers
from aiogram import Bot
from redis.asyncio import Redis

from src.application.services.custom_question_admin import CustomQuestionAdminService
from src.application.services.admin_users import AdminUserService
from src.application.services.notification import NotificationService
from src.application.services.profile_completion import ProfileCompletionService
from src.application.services.questionnaire import QuestionnaireService
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
from src.application.services.subscription import SubscriptionService
from src.application.services.value_casting import LenientCaster
from src.application.use_cases.payment.cryptobot import CryptoBotPaymentUseCase
from src.application.use_cases.workout_generator.simple_matcher import SimpleWorkoutMatcher
from src.presentation.telegram_bot.flows.questionnaire.flow_service import QuestionnaireFlow
from src.presentation.telegram_bot.flows.questionnaire.presenter import QuestionnairePresenter
from src.presentation.telegram_bot.flows.workouts.flow_service import WorkoutsFlow
from src.presentation.telegram_bot.flows.workouts.link_map_builder import LinkMapBuilder
from src.presentation.telegram_bot.flows.workouts.presenter import WorkoutPlanPresenter
from src.presentation.web_admin.question_controller import QuestionController
from src.presentation.web_admin.question_presenters import (
    OptionsNormalizer,
    QuestionPayloadBuilder,
    QuestionPresenter,
)
from src.presentation.web_admin.user_controller import UserController
from src.presentation.web_admin.user_presenters import UserPresenter
from src.shared.utils.profile_answers import AnswerLookup
from src.infrastructure.cache.redis_repository import RedisCache
from src.infrastructure.database.session import create_engine, create_session_factory
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.external.cryptobot.client import CryptoBotClient
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
    wiring_config = containers.WiringConfiguration(
        packages=["src.presentation.telegram_bot.handlers", "src.presentation.web_admin"]
    )

    settings = providers.Singleton(get_settings)

    engine = providers.Singleton(create_engine)
    session_factory = providers.Singleton(create_session_factory, engine=engine)
    uow = providers.Factory(SQLAlchemyUnitOfWork, session_factory=session_factory)

    bot = providers.Singleton(Bot, token=providers.Callable(lambda: get_settings().bot.token))
    redis = providers.Singleton(Redis.from_url, url=providers.Callable(lambda: get_settings().redis.url))
    cache = providers.Factory(RedisCache, client=redis)

    cryptobot_client = providers.Singleton(
        CryptoBotClient,
        api_token=providers.Callable(lambda: get_settings().cryptobot.api_token),
        webhook_secret=providers.Callable(lambda: get_settings().cryptobot.webhook_secret),
    )
    minio_storage = providers.Singleton(
        MinioStorage,
        endpoint=providers.Callable(lambda: get_settings().minio.endpoint),
        access_key=providers.Callable(lambda: get_settings().minio.access_key),
        secret_key=providers.Callable(lambda: get_settings().minio.secret_key),
        secure=providers.Callable(lambda: get_settings().minio.secure),
    )

    notifier = providers.Factory(TelegramNotifier, bot=bot)
    notification_service = providers.Factory(NotificationService, notifier=notifier)
    subscription_service = providers.Factory(SubscriptionService)

    payment_use_case = providers.Factory(
        CryptoBotPaymentUseCase,
        gateway=cryptobot_client,
        uow=uow,
        subscription_service=subscription_service,
        notification_service=notification_service,
    )

    value_caster = providers.Singleton(LenientCaster)
    answer_lookup_builder = providers.Callable(
        lambda caster: (lambda answers: AnswerLookup(answers, caster=caster)),
        caster=value_caster,
    )
    workout_matcher = providers.Factory(
        SimpleWorkoutMatcher,
        lookup_factory=answer_lookup_builder,
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
    questionnaire_service = providers.Factory(
        QuestionnaireService,
        uow=uow,
        validator=answer_validator,
        factory=question_factory,
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
    )

    workout_plan_presenter = providers.Factory(WorkoutPlanPresenter)
    link_map_builder = providers.Factory(LinkMapBuilder)
    workouts_flow = providers.Factory(
        WorkoutsFlow,
        uow=uow,
        matcher=workout_matcher,
        presenter=workout_plan_presenter,
        link_map_builder=link_map_builder,
    )

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


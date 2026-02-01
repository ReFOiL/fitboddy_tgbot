from aiogram.fsm.state import State, StatesGroup


class QuestionnaireStates(StatesGroup):
    in_progress = State()


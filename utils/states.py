from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    broadcast = State()
    ban_user = State()
    unban_user = State()

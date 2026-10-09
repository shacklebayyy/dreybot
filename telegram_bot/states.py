from aiogram.fsm.state import State, StatesGroup

class CustomRequestState(StatesGroup):
    waiting_for_details = State()

class SupportState(StatesGroup):
    waiting_for_message = State()

class TopUpState(StatesGroup):
    waiting_for_custom_amount = State()
    waiting_for_proof = State()

class VerificationState(StatesGroup):
    waiting_for_user_data = State()

class AdminState(StatesGroup):
    waiting_for_ticket_reply = State()
    waiting_for_order_doc = State()
    waiting_for_broadcast = State()
    waiting_for_service_price = State()
    waiting_for_verif_result = State()


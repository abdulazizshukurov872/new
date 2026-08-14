from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    name = State()
    email = State()
    password = State()
    confirm_password = State()


class LoginStates(StatesGroup):
    email = State()
    password = State()


class SearchStates(StatesGroup):
    query = State()
    district = State()


class FilterStates(StatesGroup):
    choosing = State()


class AIStates(StatesGroup):
    query = State()


class BookingStates(StatesGroup):
    date = State()
    start_time = State()
    end_time = State()
    seat = State()
    confirm = State()


class ReviewStates(StatesGroup):
    rating = State()
    wifi_rating = State()
    noise_rating = State()
    comfort_rating = State()
    comment = State()


class AddPlaceStates(StatesGroup):
    name = State()
    description = State()
    type = State()
    address = State()
    district = State()
    latitude = State()
    longitude = State()
    price = State()
    wifi_speed = State()
    noise_level = State()
    sockets = State()
    capacity = State()
    working_hours = State()
    amenities = State()
    confirm = State()


class ContactAdminStates(StatesGroup):
    message = State()


class AdminPanelStates(StatesGroup):
    role_user_query = State()
    block_user_query = State()
    unblock_user_query = State()
    broadcast_text = State()
    broadcast_confirm = State()

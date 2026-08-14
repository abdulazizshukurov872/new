from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import get_session
from bot.keyboards import get_menu_kb, guest_menu_kb, login_prompt_kb, profile_kb
from bot.services.admin import check_admin, promote_if_admin
from bot.services.auth import (
    get_user_by_telegram,
    is_authenticated,
    login_user,
    logout_user,
    register_user,
)
from bot.states import LoginStates, RegisterStates

router = Router()


def _user_menu(session, telegram_id: int, username: str | None):
    promote_if_admin(session, telegram_id, username)
    logged_in = is_authenticated(session, telegram_id)
    admin = check_admin(session, telegram_id, username)
    return get_menu_kb(logged_in, admin)


async def _send_logout_success(message: Message, was_active: bool) -> None:
    if was_active:
        text = (
            "🚪 <b>Tizimdan chiqdingiz!</b>\n\n"
            "Endi guest rejimdasiz — joylarni ko'rish va qidirish mumkin.\n"
            "Qayta kirish: 🔐 Kirish"
        )
    else:
        text = (
            "✅ <b>Guest rejim</b>\n\n"
            "Siz tizimga kirmagansiz. Klaviatura yangilandi."
        )
    await message.answer(text, reply_markup=guest_menu_kb(), parse_mode="HTML")


@router.message(F.text == "📝 Ro'yxatdan o'tish")
@router.callback_query(F.data == "register:start")
async def start_register(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
        telegram_id = event.from_user.id
    else:
        message = event
        telegram_id = message.from_user.id

    session = get_session()
    try:
        if is_authenticated(session, telegram_id):
            kb = _user_menu(session, telegram_id, message.from_user.username if isinstance(event, Message) else event.from_user.username)
            await message.answer("Siz allaqachon tizimga kirdingiz!", reply_markup=kb)
            return
    finally:
        session.close()

    await state.set_state(RegisterStates.name)
    await message.answer(
        "📝 <b>Ro'yxatdan o'tish</b>\n\nIsmingizni kiriting:",
        parse_mode="HTML",
    )


@router.message(RegisterStates.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(RegisterStates.email)
    await message.answer("📧 Email manzilingizni kiriting:")


@router.message(RegisterStates.email)
async def register_email(message: Message, state: FSMContext):
    email = message.text.strip().lower()
    if "@" not in email or "." not in email:
        await message.answer("Noto'g'ri email. Qaytadan kiriting:")
        return

    await state.update_data(email=email)
    await state.set_state(RegisterStates.password)
    await message.answer("🔑 Parol o'rnating (kamida 6 ta belgi):")


@router.message(RegisterStates.password)
async def register_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 6:
        await message.answer("Parol kamida 6 ta belgidan iborat bo'lishi kerak:")
        return

    await state.update_data(password=password)
    await state.set_state(RegisterStates.confirm_password)
    await message.answer("🔑 Parolni qayta kiriting:")


@router.message(RegisterStates.confirm_password)
async def register_confirm_password(message: Message, state: FSMContext):
    confirm = message.text.strip()
    data = await state.get_data()

    if confirm != data.get("password"):
        await message.answer("Parollar mos kelmadi. Qaytadan parol o'rnating:")
        await state.set_state(RegisterStates.password)
        return

    session = get_session()
    try:
        try:
            register_user(session, message.from_user.id, data["name"], data["email"], data["password"])
        except ValueError as e:
            await message.answer(f"❌ {e}")
            return

        await state.clear()
        kb = _user_menu(session, message.from_user.id, message.from_user.username)
        await message.answer(
            "✅ <b>Ro'yxatdan o'tdingiz va tizimga kirdingiz!</b>\n\n"
            "Endi booking, sharh va sevimlilar ishlatish mumkin.",
            reply_markup=kb,
            parse_mode="HTML",
        )
    finally:
        session.close()


@router.message(F.text == "🔐 Kirish")
@router.message(Command("login"))
@router.callback_query(F.data == "login:start")
async def start_login(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
        telegram_id = event.from_user.id
    else:
        message = event
        telegram_id = event.from_user.id

    session = get_session()
    try:
        if is_authenticated(session, telegram_id):
            kb = _user_menu(session, telegram_id, message.from_user.username if isinstance(event, Message) else event.from_user.username)
            await message.answer("Siz allaqachon tizimga kirdingiz!", reply_markup=kb)
            return
    finally:
        session.close()

    await state.set_state(LoginStates.email)
    await message.answer(
        "🔐 <b>Kirish</b>\n\nEmail manzilingizni kiriting:",
        parse_mode="HTML",
    )


@router.message(LoginStates.email)
async def login_email(message: Message, state: FSMContext):
    email = message.text.strip().lower()
    if "@" not in email or "." not in email:
        await message.answer("Noto'g'ri email. Qaytadan kiriting:")
        return

    await state.update_data(email=email)
    await state.set_state(LoginStates.password)
    await message.answer("🔑 Parolingizni kiriting:")


@router.message(LoginStates.password)
async def login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    try:
        try:
            user = login_user(session, message.from_user.id, data["email"], message.text.strip())
        except ValueError as e:
            await message.answer(f"❌ {e}", reply_markup=login_prompt_kb())
            return

        await state.clear()
        kb = _user_menu(session, message.from_user.id, message.from_user.username)
        await message.answer(
            f"✅ <b>Xush kelibsiz, {user.name}!</b>\n\nTizimga muvaffaqiyatli kirdingiz.",
            reply_markup=kb,
            parse_mode="HTML",
        )
    finally:
        session.close()


@router.message(F.text == "🚪 Chiqish")
@router.message(Command("logout"))
@router.callback_query(F.data == "logout:confirm")
async def do_logout(event: Message | CallbackQuery, state: FSMContext):
    if isinstance(event, CallbackQuery):
        await event.answer("Chiqildi ✅")
        message = event.message
        telegram_id = event.from_user.id
    else:
        message = event
        telegram_id = message.from_user.id

    await state.clear()
    session = get_session()
    try:
        was_active = logout_user(session, telegram_id)
    finally:
        session.close()

    await _send_logout_success(message, was_active)


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message):
    session = get_session()
    try:
        if not is_authenticated(session, message.from_user.id):
            await message.answer(
                "Profilni ko'rish uchun avval tizimga kiring.",
                reply_markup=login_prompt_kb(),
            )
            return

        user = get_user_by_telegram(session, message.from_user.id)
        from bot.database.models import Booking, Favorite

        bookings_count = session.query(Booking).filter(Booking.user_id == user.id).count()
        fav_count = session.query(Favorite).filter(Favorite.user_id == user.id).count()

        await message.answer(
            f"👤 <b>Profil</b>\n\n"
            f"📛 Ism: {user.name}\n"
            f"📧 Email: {user.email}\n"
            f"📅 Bookinglar: {bookings_count}\n"
            f"❤️ Sevimlilar: {fav_count}\n"
            f"📆 Ro'yxatdan o'tgan: {user.created_at.strftime('%d.%m.%Y')}",
            parse_mode="HTML",
            reply_markup=profile_kb(),
        )
    finally:
        session.close()

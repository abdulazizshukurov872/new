from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import ADMIN_USERNAME
from bot.database.models import User, get_session
from bot.keyboards import back_kb, contact_admin_block_kb, get_menu_kb
from bot.services.admin import check_admin, get_admin_telegram_ids
from bot.states import ContactAdminStates

router = Router()


@router.message(F.text == "📩 Adminga xabar")
async def start_contact_admin(message: Message, state: FSMContext):
    session = get_session()
    try:
        if check_admin(session, message.from_user.id, message.from_user.username):
            await message.answer("Siz adminsiz. Foydalanuvchilar sizga xabar yuboradi.")
            return
    finally:
        session.close()

    await state.set_state(ContactAdminStates.message)
    await message.answer(
        "📩 <b>Adminga xabar</b>\n\n"
        f"Xabaringizni yozing — adminlarga (@{ADMIN_USERNAME} va boshqalar) yuboriladi.\n\n"
        "Masalan: yangi kutubxona qo'shishni taklif qilish, muammo haqida yozish.",
        parse_mode="HTML",
        reply_markup=back_kb(),
    )


@router.message(ContactAdminStates.message)
async def send_to_admin(message: Message, state: FSMContext):
    if message.text == "🏠 Bosh menyu":
        await state.clear()
        from bot.handlers.start import cmd_help
        await cmd_help(message)
        return

    text = message.text.strip()
    if not text:
        await message.answer("Xabar bo'sh bo'lmasligi kerak.")
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "yo'q"
    full_name = user.full_name or "Noma'lum"

    admin_text = (
        "📩 <b>Yangi xabar (QuietSpace bot)</b>\n\n"
        f"👤 Ism: {full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 Telegram ID: <code>{user.id}</code>\n\n"
        f"💬 <b>Xabar:</b>\n{text}"
    )

    session = get_session()
    try:
        admin_ids = get_admin_telegram_ids(session)
        db_user = session.query(User).filter(User.telegram_id == user.id).first()
        is_blocked = db_user is not None and not db_user.is_active
        block_kb = contact_admin_block_kb(user.id, is_blocked) if db_user and db_user.role != "admin" else None

        sent = 0
        for admin_id in admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    admin_text,
                    parse_mode="HTML",
                    reply_markup=block_kb,
                )
                sent += 1
            except Exception:
                pass

        if sent == 0:
            await message.answer(
                "❌ Xabar yuborilmadi. Keyinroq qayta urinib ko'ring.",
                reply_markup=back_kb(),
            )
            return

        await state.clear()
        from bot.services.auth import is_authenticated

        logged_in = is_authenticated(session, user.id)
        admin = check_admin(session, user.id, user.username)

        await message.answer(
            "✅ Xabaringiz adminlarga yuborildi!\nTez orada javob olasiz.",
            reply_markup=get_menu_kb(logged_in, admin),
        )
    finally:
        session.close()

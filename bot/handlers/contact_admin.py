import logging
from html import escape

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User as TgUser

from bot.config import ADMIN_USERNAME
from bot.database.models import User, get_session
from bot.keyboards import back_kb, contact_admin_block_kb, get_menu_kb
from bot.services.admin import check_admin, get_admin_telegram_ids
from bot.states import ContactAdminStates

router = Router()
logger = logging.getLogger(__name__)


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


def _extract_message_text(message: Message) -> str:
    if message.text:
        return message.text.strip()
    if message.caption:
        return message.caption.strip()
    return ""


def _build_admin_text(user: TgUser, text: str) -> str:
    username = f"@{user.username}" if user.username else "yo'q"
    full_name = user.full_name or "Noma'lum"
    safe_text = escape(text) if text else "—"

    return (
        "📩 <b>Yangi xabar (QuietSpace bot)</b>\n\n"
        f"👤 Ism: {escape(full_name)}\n"
        f"🔗 Username: {escape(username)}\n"
        f"🆔 Telegram ID: <code>{user.id}</code>\n\n"
        f"💬 <b>Xabar:</b>\n{safe_text}"
    )


async def _send_to_admin(message: Message, admin_id: int, admin_text: str, block_kb) -> bool:
    try:
        await message.bot.send_message(
            admin_id,
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=block_kb,
        )
        return True
    except Exception as e:
        logger.error("Admin %s ga HTML xabar yuborilmadi: %s", admin_id, e)
        try:
            plain = admin_text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
            await message.bot.send_message(
                admin_id,
                plain,
                parse_mode=None,
                reply_markup=block_kb,
            )
            return True
        except Exception as e2:
            logger.error("Admin %s ga oddiy xabar ham yuborilmadi: %s", admin_id, e2)
            return False


@router.message(ContactAdminStates.message)
async def send_to_admin(message: Message, state: FSMContext):
    if message.text == "🏠 Bosh menyu":
        await state.clear()
        from bot.handlers.start import cmd_help
        await cmd_help(message)
        return

    text = _extract_message_text(message)
    if not text and not message.photo and not message.document and not message.voice:
        await message.answer("Xabar bo'sh bo'lmasligi kerak. Matn yuboring.")
        return

    user = message.from_user
    admin_text = _build_admin_text(user, text or "(media xabar)")

    session = get_session()
    try:
        admin_ids = get_admin_telegram_ids(session)
        if not admin_ids:
            logger.error("Admin ID lar topilmadi!")
            await message.answer(
                "❌ Admin topilmadi. Keyinroq qayta urinib ko'ring.",
                reply_markup=back_kb(),
            )
            return

        db_user = session.query(User).filter(User.telegram_id == user.id).first()
        is_blocked = db_user is not None and not db_user.is_active
        block_kb = contact_admin_block_kb(user.id, is_blocked) if db_user and db_user.role != "admin" else None

        sent = 0
        for admin_id in admin_ids:
            if admin_id == user.id:
                continue
            if await _send_to_admin(message, admin_id, admin_text, block_kb):
                sent += 1

            if message.photo:
                try:
                    await message.bot.send_photo(
                        admin_id,
                        message.photo[-1].file_id,
                        caption=f"📎 {user.full_name or user.id} dan rasm",
                        parse_mode=None,
                    )
                except Exception as e:
                    logger.error("Admin %s ga rasm yuborilmadi: %s", admin_id, e)

        if sent == 0:
            await message.answer(
                "❌ Xabar yuborilmadi. Admin botni /start qilgan bo'lishi kerak.",
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

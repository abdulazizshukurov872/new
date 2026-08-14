from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.database.models import get_session
from bot.keyboards import get_menu_kb
from bot.services.admin import check_admin, promote_if_admin, setup_admin
from bot.services.auth import is_authenticated

router = Router()


def _get_menu(session, telegram_id: int, username: str | None):
    promote_if_admin(session, telegram_id, username)
    logged_in = is_authenticated(session, telegram_id)
    admin = check_admin(session, telegram_id, username)
    return get_menu_kb(logged_in, admin), admin


@router.message(CommandStart())
async def cmd_start(message: Message):
    session = get_session()
    try:
        setup_admin(session)
        kb, admin = _get_menu(session, message.from_user.id, message.from_user.username)
    finally:
        session.close()

    admin_note = "\n\n👑 <b>Siz admin sifatida kirdingiz.</b>" if admin else ""

    await message.answer(
        "👋 <b>QuietSpace Tashkent</b> ga xush kelibsiz!\n\n"
        "Toshkentda tinch, qulay va ishlashga mos joylarni toping.\n\n"
        "🔓 <b>Ro'yxatdan o'tmasdan:</b>\n"
        "• Joylarni ko'rish va qidirish\n"
        "• Lokatsiya yuborib yaqin joylarni topish\n"
        "• Haqiqiy kutubxonalar ro'yxati\n"
        "• Filter va xarita\n"
        "• 📩 Adminga xabar yuborish\n\n"
        "🔐 <b>Login qilgandan keyin:</b>\n"
        "• Booking, sharh, sevimlilar\n\n"
        f"🏠 Asosiy CTA: <i>Find a quiet place to work</i>{admin_note}",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.message(Command("help"))
@router.message(lambda m: m.text == "🏠 Bosh menyu")
async def cmd_help(message: Message):
    session = get_session()
    try:
        kb, _ = _get_menu(session, message.from_user.id, message.from_user.username)
    finally:
        session.close()

    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "🔍 <b>Joy qidirish</b> — nom, tuman yoki manzil bo'yicha\n"
        "📋 <b>Barcha joylar</b> — barcha tasdiqlangan joylar\n"
        "📍 <b>Yaqinimdagi joylar</b> — lokatsiya yuboring\n"
        "📚 <b>Yaqin kutubxonalar</b> — haqiqiy kutubxonalar\n"
        "📩 <b>Adminga xabar</b> — taklif yoki savol yuborish\n"
        "🔐 <b>Kirish</b> / 🚪 <b>Chiqish</b>\n"
        "➕ <b>Joy qo'shish</b> — faqat admin uchun\n\n"
        "Misol: <i>Yunusobodda tinch va Wi-Fi tez joy topish</i>",
        reply_markup=kb,
        parse_mode="HTML",
    )

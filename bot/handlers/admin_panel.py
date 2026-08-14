from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import get_session
from bot.keyboards import (
    admin_panel_kb,
    broadcast_confirm_kb,
    contact_admin_block_kb,
    role_select_kb,
    user_actions_kb,
    users_manage_kb,
)
from bot.services.admin import (
    block_user,
    check_admin,
    find_user,
    get_all_users,
    get_broadcast_users,
    get_stats,
    set_user_role,
    unblock_user,
)
from bot.states import AdminPanelStates

router = Router()


def _require_admin(session, telegram_id: int, username: str | None) -> bool:
    return check_admin(session, telegram_id, username)


def _user_line(user) -> str:
    status = "✅" if user.is_active else "🚫"
    role = "👑" if user.role == "admin" else "👤"
    return (
        f"{status} {role} <b>{user.name}</b>\n"
        f"   ID: <code>{user.telegram_id}</code> | {user.email or '—'}"
    )


def _users_list_text(users) -> str:
    if not users:
        return "👥 Hozircha foydalanuvchilar yo'q."
    lines = [
        "👥 <b>Foydalanuvchilar</b>\n",
        "Bloklash yoki chiqarish uchun tugmani bosing:\n",
    ]
    lines.extend(_user_line(u) for u in users)
    return "\n".join(lines)


async def _refresh_users_list(callback: CallbackQuery, session) -> None:
    users = get_all_users(session)
    await callback.message.edit_text(
        _users_list_text(users),
        parse_mode="HTML",
        reply_markup=users_manage_kb(users),
    )


@router.message(F.text == "👑 Admin panel")
async def open_admin_panel(message: Message, state: FSMContext):
    session = get_session()
    try:
        if not _require_admin(session, message.from_user.id, message.from_user.username):
            await message.answer("❌ Bu bo'lim faqat adminlar uchun.")
            return
    finally:
        session.close()

    await state.clear()
    await message.answer(
        "👑 <b>Admin panel</b>\n\n"
        "Quyidagi funksiyalardan foydalaning:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "adm:close")
async def close_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "adm:back")
async def back_to_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👑 <b>Admin panel</b>\n\nQuyidagi funksiyalardan foydalaning:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:stats")
async def show_stats(callback: CallbackQuery):
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        stats = get_stats(session)
        text = (
            "📊 <b>Statistika</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{stats['users']}</b>\n"
            f"✅ Faol: <b>{stats['active_users']}</b>\n"
            f"🚫 Bloklangan: <b>{stats['blocked_users']}</b>\n"
            f"👑 Adminlar: <b>{stats['admins']}</b>\n\n"
            f"📍 Joylar: <b>{stats['places']}</b>\n"
            f"📅 Bookinglar: <b>{stats['bookings']}</b>\n"
            f"⭐ Sharhlar: <b>{stats['reviews']}</b>\n"
            f"❤️ Sevimlilar: <b>{stats['favorites']}</b>"
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_panel_kb())
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data == "adm:users")
async def show_users(callback: CallbackQuery):
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        users = get_all_users(session)
        await callback.message.edit_text(
            _users_list_text(users),
            parse_mode="HTML",
            reply_markup=users_manage_kb(users),
        )
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data.startswith("adm:userinfo:"))
async def show_user_info(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[2])
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        user = find_user(session, str(telegram_id))
        if not user:
            await callback.answer("Topilmadi", show_alert=True)
            return

        status = "✅ Faol" if user.is_active else "🚫 Bloklangan"
        text = (
            f"👤 <b>{user.name}</b>\n\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"📧 Email: {user.email or '—'}\n"
            f"👑 Rol: <b>{user.role}</b>\n"
            f"📌 Holat: <b>{status}</b>"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=user_actions_kb(user),
        )
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data.startswith("adm:blockid:"))
async def block_user_by_button(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[2])
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        user = find_user(session, str(telegram_id))
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return

        try:
            block_user(session, user)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return

        session.refresh(user)
        await callback.answer(f"🚫 {user.name} bloklandi", show_alert=True)

        if callback.message.text and "Foydalanuvchilar" in callback.message.text:
            await _refresh_users_list(callback, session)
        elif callback.message.text and callback.message.text.startswith("👤"):
            status = "🚫 Bloklangan"
            text = (
                f"👤 <b>{user.name}</b>\n\n"
                f"🆔 ID: <code>{user.telegram_id}</code>\n"
                f"📧 Email: {user.email or '—'}\n"
                f"👑 Rol: <b>{user.role}</b>\n"
                f"📌 Holat: <b>{status}</b>"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=user_actions_kb(user))
        else:
            await callback.message.edit_reply_markup(reply_markup=contact_admin_block_kb(user.telegram_id, True))
    finally:
        session.close()


@router.callback_query(F.data.startswith("adm:unblockid:"))
async def unblock_user_by_button(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[2])
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        user = find_user(session, str(telegram_id))
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return

        unblock_user(session, user)
        session.refresh(user)
        await callback.answer(f"✅ {user.name} chiqarildi", show_alert=True)

        if callback.message.text and "Foydalanuvchilar" in callback.message.text:
            await _refresh_users_list(callback, session)
        elif callback.message.text and callback.message.text.startswith("👤"):
            status = "✅ Faol"
            text = (
                f"👤 <b>{user.name}</b>\n\n"
                f"🆔 ID: <code>{user.telegram_id}</code>\n"
                f"📧 Email: {user.email or '—'}\n"
                f"👑 Rol: <b>{user.role}</b>\n"
                f"📌 Holat: <b>{status}</b>"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=user_actions_kb(user))
        else:
            await callback.message.edit_reply_markup(reply_markup=contact_admin_block_kb(user.telegram_id, False))
    finally:
        session.close()


@router.callback_query(F.data == "adm:role")
async def start_role_change(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return
    finally:
        session.close()

    await state.set_state(AdminPanelStates.role_user_query)
    await callback.message.answer(
        "🔄 <b>Rol o'zgartirish</b>\n\n"
        "Foydalanuvchi <b>Telegram ID</b> yoki <b>email</b>ini yuboring:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminPanelStates.role_user_query)
async def role_user_query(message: Message, state: FSMContext):
    session = get_session()
    try:
        if not _require_admin(session, message.from_user.id, message.from_user.username):
            await message.answer("❌ Ruxsat yo'q.")
            await state.clear()
            return

        user = find_user(session, message.text or "")
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi. Qayta urinib ko'ring.")
            return

        await state.clear()
        await message.answer(
            f"Foydalanuvchi: <b>{user.name}</b>\n"
            f"ID: <code>{user.telegram_id}</code>\n"
            f"Hozirgi rol: <b>{user.role}</b>\n\n"
            "Yangi rolni tanlang:",
            parse_mode="HTML",
            reply_markup=role_select_kb(user.telegram_id),
        )
    finally:
        session.close()


@router.callback_query(F.data.startswith("adm:setrole:"))
async def apply_role(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Xato", show_alert=True)
        return

    telegram_id = int(parts[2])
    role = parts[3]

    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        user = find_user(session, str(telegram_id))
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return

        try:
            set_user_role(session, user, role)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return

        await callback.answer(f"✅ Rol: {role}", show_alert=True)

        if callback.message.text and callback.message.text.startswith("👤"):
            status = "✅ Faol" if user.is_active else "🚫 Bloklangan"
            text = (
                f"👤 <b>{user.name}</b>\n\n"
                f"🆔 ID: <code>{user.telegram_id}</code>\n"
                f"📧 Email: {user.email or '—'}\n"
                f"👑 Rol: <b>{user.role}</b>\n"
                f"📌 Holat: <b>{status}</b>"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=user_actions_kb(user))
        else:
            await callback.message.edit_text(
                f"✅ <b>{user.name}</b> roli <b>{role}</b> ga o'zgartirildi.",
                parse_mode="HTML",
                reply_markup=admin_panel_kb(),
            )
    finally:
        session.close()


@router.callback_query(F.data == "adm:broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return
    finally:
        session.close()

    await state.set_state(AdminPanelStates.broadcast_text)
    await callback.message.answer(
        "📢 <b>Reklama yuborish</b>\n\n"
        "Barcha faol foydalanuvchilarga yuboriladigan xabarni yozing.\n"
        "HTML format qo'llab-quvvatlanadi.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminPanelStates.broadcast_text)
async def broadcast_preview(message: Message, state: FSMContext):
    text = message.text or message.caption or ""
    if not text.strip():
        await message.answer("❌ Xabar bo'sh bo'lmasligi kerak.")
        return

    session = get_session()
    try:
        if not _require_admin(session, message.from_user.id, message.from_user.username):
            await message.answer("❌ Ruxsat yo'q.")
            await state.clear()
            return

        count = len(get_broadcast_users(session))
        await state.update_data(broadcast_text=text)
        await state.set_state(AdminPanelStates.broadcast_confirm)
        await message.answer(
            f"📢 <b>Reklama ko'rinishi:</b>\n\n{text}\n\n"
            f"👥 <b>{count}</b> ta faol foydalanuvchiga yuboriladi.\n"
            "Tasdiqlaysizmi?",
            parse_mode="HTML",
            reply_markup=broadcast_confirm_kb(),
        )
    finally:
        session.close()


@router.callback_query(F.data == "adm:bcancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Reklama bekor qilindi.", reply_markup=admin_panel_kb())
    await callback.answer()


@router.callback_query(F.data == "adm:bsend")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    try:
        if not _require_admin(session, callback.from_user.id, callback.from_user.username):
            await callback.answer("Ruxsat yo'q", show_alert=True)
            return

        data = await state.get_data()
        text = data.get("broadcast_text", "")
        if not text:
            await callback.answer("Xabar topilmadi", show_alert=True)
            return

        users = get_broadcast_users(session)
        sent = 0
        failed = 0
        for user in users:
            if user.telegram_id == callback.from_user.id:
                continue
            try:
                await callback.bot.send_message(user.telegram_id, text, parse_mode="HTML")
                sent += 1
            except Exception:
                failed += 1

        await state.clear()
        await callback.message.edit_text(
            f"✅ Reklama yuborildi!\n\n"
            f"📤 Yuborildi: <b>{sent}</b>\n"
            f"❌ Xato: <b>{failed}</b>",
            parse_mode="HTML",
            reply_markup=admin_panel_kb(),
        )
    finally:
        session.close()
    await callback.answer()

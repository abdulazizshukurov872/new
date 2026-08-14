from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.orm import joinedload

from bot.database.models import Favorite, get_session
from bot.keyboards import login_prompt_kb, place_card_kb
from bot.services.auth import get_user_by_telegram, is_authenticated
from bot.services.places import format_place_short, get_place

router = Router()


@router.message(F.text == "❤️ Sevimlilar")
async def list_favorites(message: Message):
    session = get_session()
    try:
        if not is_authenticated(session, message.from_user.id):
            await message.answer(
                "Sevimlilar uchun tizimga kiring.",
                reply_markup=login_prompt_kb(),
            )
            return

        user = get_user_by_telegram(session, message.from_user.id)

        favorites = (
            session.query(Favorite)
            .options(joinedload(Favorite.place))
            .filter(Favorite.user_id == user.id)
            .all()
        )
        if not favorites:
            await message.answer("Sevimlilar ro'yxati bo'sh.")
            return

        await message.answer(
            f"❤️ <b>Sevimlilar</b> ({len(favorites)} ta):",
            parse_mode="HTML",
        )
        for fav in favorites:
            if not fav.place:
                continue
            await message.answer(
                format_place_short(fav.place),
                reply_markup=place_card_kb(fav.place_id, True, True),
                parse_mode="HTML",
            )
    except Exception:
        await message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")
    finally:
        session.close()


@router.callback_query(F.data.startswith("fav:"))
async def toggle_favorite(callback: CallbackQuery):
    try:
        place_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    session = get_session()
    try:
        if not is_authenticated(session, callback.from_user.id):
            await callback.answer()
            await callback.message.answer(
                "❤️ Sevimlilarga qo'shish uchun tizimga kiring:",
                reply_markup=login_prompt_kb(),
            )
            return

        user = get_user_by_telegram(session, callback.from_user.id)

        existing = (
            session.query(Favorite)
            .filter(Favorite.user_id == user.id, Favorite.place_id == place_id)
            .first()
        )

        if existing:
            session.delete(existing)
            session.commit()
            await callback.answer("Sevimlilardan olib tashlandi.")
        else:
            place = get_place(session, place_id)
            if not place:
                await callback.answer("Joy topilmadi.", show_alert=True)
                return
            session.add(Favorite(user_id=user.id, place_id=place_id))
            session.commit()
            await callback.answer("Sevimlilarga qo'shildi ❤️")
    except Exception:
        session.rollback()
        await callback.answer("Xatolik yuz berdi. Qayta urinib ko'ring.", show_alert=True)
    finally:
        session.close()

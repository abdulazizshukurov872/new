from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.database.models import get_session
from bot.keyboards import filter_main_kb, place_card_kb, places_list_kb
from bot.services.auth import get_user_by_telegram, is_authenticated
from bot.services.places import (
    format_place_detail,
    format_place_short,
    get_available_places,
    get_place,
    get_popular_places,
    is_favorite,
    search_places,
)

router = Router()

_user_filters: dict[int, dict] = {}


def _get_filters(user_id: int) -> dict:
    if user_id not in _user_filters:
        _user_filters[user_id] = {}
    return _user_filters[user_id]


@router.message(F.text == "📋 Barcha joylar")
async def list_all_places(message: Message):
    session = get_session()
    try:
        places = search_places(session)
        if not places:
            await message.answer("Hozircha joylar mavjud emas.")
            return

        await message.answer(
            f"📋 <b>Barcha joylar</b> ({len(places)} ta)\n\nJoyni tanlang:",
            reply_markup=places_list_kb(places),
            parse_mode="HTML",
        )
    finally:
        session.close()


@router.message(F.text == "⭐ Mashhur joylar")
async def popular_places(message: Message):
    session = get_session()
    try:
        places = get_popular_places(session)
        text = "⭐ <b>Mashhur joylar</b>\n\n"
        for p in places:
            text += format_place_short(p) + "\n\n─────────────\n\n"

        reg = is_authenticated(session, message.from_user.id)
        user = get_user_by_telegram(session, message.from_user.id) if reg else None

        await message.answer(text.strip(), parse_mode="HTML")
        for p in places:
            fav = is_favorite(session, user.id, p.id) if reg and user else False
            await message.answer(
                f"📍 {p.name}",
                reply_markup=place_card_kb(p.id, fav, reg),
            )
    finally:
        session.close()


@router.message(F.text == "🗺 Xarita")
async def map_view(message: Message):
    session = get_session()
    try:
        places = search_places(session, available_only=True)
        if not places:
            await message.answer("Xaritada ko'rsatish uchun joylar yo'q.")
            return

        text = "🗺 <b>Joylar xaritasi</b>\n\nHar bir joy uchun xarita havolasini bosing:\n\n"
        for p in places:
            text += (
                f"📍 <b>{p.name}</b> — {p.district.title()}\n"
                f"   https://www.openstreetmap.org/?mlat={p.latitude}&mlon={p.longitude}#map=16/{p.latitude}/{p.longitude}\n\n"
            )

        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    finally:
        session.close()


@router.message(F.text == "🔧 Filter")
async def filter_menu(message: Message):
    await message.answer(
        "🔧 <b>Filter</b>\n\nKerakli filterni tanlang:",
        reply_markup=filter_main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("page:"))
async def paginate_places(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    session = get_session()
    try:
        filters = _get_filters(callback.from_user.id)
        places = search_places(session, **filters)
        await callback.message.edit_reply_markup(reply_markup=places_list_kb(places, page))
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data == "places:list")
async def back_to_places(callback: CallbackQuery):
    session = get_session()
    try:
        places = search_places(session)
        await callback.message.edit_text(
            f"📋 <b>Barcha joylar</b> ({len(places)} ta)",
            reply_markup=places_list_kb(places),
            parse_mode="HTML",
        )
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data.startswith("place:"))
async def show_place_detail(callback: CallbackQuery):
    place_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        place = get_place(session, place_id)
        if not place:
            await callback.answer("Joy topilmadi.", show_alert=True)
            return

        reg = is_authenticated(session, callback.from_user.id)
        user = get_user_by_telegram(session, callback.from_user.id) if reg else None
        fav = is_favorite(session, user.id, place_id) if reg and user else False

        text = format_place_detail(place, session)
        await callback.message.edit_text(
            text,
            reply_markup=place_detail_kb(place_id, fav, reg),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data.startswith("map:"))
async def show_map_link(callback: CallbackQuery):
    place_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        place = get_place(session, place_id)
        if place:
            url = f"https://www.openstreetmap.org/?mlat={place.latitude}&mlon={place.longitude}#map=17/{place.latitude}/{place.longitude}"
            await callback.answer()
            await callback.message.answer(
                f"🗺 <b>{place.name}</b>\n{url}",
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
    finally:
        session.close()


# Filter callbacks
@router.callback_query(F.data.startswith("filter:"))
async def handle_filter(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id
    filters = _get_filters(user_id)
    session = get_session()

    try:
        if action == "back":
            await callback.message.edit_text(
                "🔧 <b>Filter</b>",
                reply_markup=filter_main_kb(),
                parse_mode="HTML",
            )
        elif action == "type":
            from bot.keyboards import filter_type_kb
            await callback.message.edit_reply_markup(reply_markup=filter_type_kb())
        elif action == "noise":
            from bot.keyboards import filter_noise_kb
            await callback.message.edit_reply_markup(reply_markup=filter_noise_kb())
        elif action == "wifi50":
            filters["min_wifi"] = 50
            places = search_places(session, **filters)
            await _show_filtered(callback, places, filters)
        elif action == "sockets":
            filters["has_sockets"] = True
            places = search_places(session, **filters)
            await _show_filtered(callback, places, filters)
        elif action == "free":
            filters["free_only"] = True
            places = search_places(session, **filters)
            await _show_filtered(callback, places, filters)
        elif action == "available":
            filters["available_only"] = True
            places = search_places(session, **filters)
            await _show_filtered(callback, places, filters)
        elif action == "clear":
            _user_filters[user_id] = {}
            places = search_places(session)
            await callback.message.edit_text(
                f"🔄 Filter tozalandi.\n\n📋 <b>Joylar</b> ({len(places)} ta)",
                reply_markup=places_list_kb(places),
                parse_mode="HTML",
            )
    finally:
        session.close()

    await callback.answer()


@router.callback_query(F.data.startswith("ftype:"))
async def filter_by_type(callback: CallbackQuery):
    ptype = callback.data.split(":")[1]
    user_id = callback.from_user.id
    filters = _get_filters(user_id)
    session = get_session()

    try:
        if ptype != "all":
            filters["place_type"] = ptype
        else:
            filters.pop("place_type", None)
        places = search_places(session, **filters)
        await _show_filtered(callback, places, filters)
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data.startswith("noise:"))
async def filter_by_noise(callback: CallbackQuery):
    noise = callback.data.split(":")[1]
    user_id = callback.from_user.id
    filters = _get_filters(user_id)
    session = get_session()

    try:
        if noise != "all":
            filters["noise_level"] = noise
        else:
            filters.pop("noise_level", None)
        places = search_places(session, **filters)
        await _show_filtered(callback, places, filters)
    finally:
        session.close()
    await callback.answer()


async def _show_filtered(callback: CallbackQuery, places: list, filters: dict):
    filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items()) or "yo'q"
    await callback.message.edit_text(
        f"🔧 Filter: {filter_desc}\n\n📋 Topildi: <b>{len(places)}</b> ta joy",
        reply_markup=places_list_kb(places),
        parse_mode="HTML",
    )


from bot.keyboards import place_detail_kb  # noqa: E402

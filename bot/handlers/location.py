from aiogram import F, Router
from aiogram.types import Message

from bot.database.models import get_session
from bot.keyboards import location_kb, place_card_kb
from bot.services.auth import get_user_by_telegram, is_authenticated
from bot.services.location import format_distance
from bot.services.places import format_place_short, get_nearby_places, is_favorite

router = Router()

_location_mode: dict[int, str] = {}  # "all" yoki "library"


@router.message(F.text == "📍 Yaqinimdagi joylar")
async def request_nearby_all(message: Message):
    _location_mode[message.from_user.id] = "all"
    await message.answer(
        "📍 <b>Yaqin atrofdagi joylar</b>\n\n"
        "Telegram orqali lokatsiyangizni yuboring.\n"
        "Pastdagi tugmani bosing 👇",
        reply_markup=location_kb(),
        parse_mode="HTML",
    )


@router.message(F.text == "📚 Yaqin kutubxonalar")
async def request_nearby_libraries(message: Message):
    _location_mode[message.from_user.id] = "library"
    await message.answer(
        "📚 <b>Yaqin kutubxonalar</b>\n\n"
        "Lokatsiyangizni yuboring — yaqin atrofdagi haqiqiy kutubxonalarni ko'rsataman.\n"
        "Pastdagi tugmani bosing 👇",
        reply_markup=location_kb(),
        parse_mode="HTML",
    )


@router.message(F.location)
async def handle_location(message: Message):
    lat = message.location.latitude
    lon = message.location.longitude
    mode = _location_mode.pop(message.from_user.id, "all")
    place_type = "library" if mode == "library" else ""

    session = get_session()
    try:
        nearby = get_nearby_places(session, lat, lon, radius_km=15.0, place_type=place_type, limit=10)
        reg = is_authenticated(session, message.from_user.id)
        user = get_user_by_telegram(session, message.from_user.id) if reg else None

        if not nearby:
            label = "kutubxona" if place_type == "library" else "joy"
            await message.answer(
                f"15 km radiusda {label} topilmadi.\n"
                "Boshqa joydan qayta urinib ko'ring yoki 📋 Barcha joylar bo'limiga qarang."
            )
            return

        title = "📚 Yaqin kutubxonalar" if place_type == "library" else "📍 Yaqin atrofdagi joylar"
        await message.answer(
            f"{title} ({len(nearby)} ta):\n"
            f"Sizning joyingiz: {lat:.4f}, {lon:.4f}",
            parse_mode="HTML",
        )

        for place, dist in nearby[:5]:
            text = format_place_short(place, distance_km=dist)
            fav = is_favorite(session, user.id, place.id) if reg and user else False
            await message.answer(
                text,
                reply_markup=place_card_kb(place.id, fav, reg),
                parse_mode="HTML",
            )
            await message.answer_location(
                latitude=place.latitude,
                longitude=place.longitude,
            )

        if len(nearby) > 5:
            rest = "\n".join(
                f"• {p.name} — {format_distance(d)}" for p, d in nearby[5:]
            )
            await message.answer(f"📋 Boshqa joylar:\n{rest}")
    finally:
        session.close()

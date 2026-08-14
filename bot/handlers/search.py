from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.models import get_session
from bot.keyboards import back_kb, place_card_kb, places_list_kb
from bot.services.auth import get_user_by_telegram, is_authenticated
from bot.services.places import format_place_short, is_favorite, search_places
from bot.states import SearchStates

router = Router()


@router.message(F.text == "🔍 Joy qidirish")
async def start_search(message: Message, state: FSMContext):
    await state.set_state(SearchStates.query)
    await message.answer(
        "🔍 <b>Qidiruv</b>\n\n"
        "Joy nomi, tuman yoki manzil kiriting.\n\n"
        "Misol: <i>Yunusobodda tinch va Wi-Fi tez joy</i>",
        parse_mode="HTML",
        reply_markup=back_kb(),
    )


@router.message(SearchStates.query)
async def process_search(message: Message, state: FSMContext):
    if message.text == "🏠 Bosh menyu":
        await state.clear()
        from bot.handlers.start import cmd_help
        await cmd_help(message)
        return

    query = message.text.strip()
    session = get_session()
    try:
        places = search_places(session, query=query)
        if not places:
            await message.answer(
                "Hech narsa topilmadi. Boshqa so'z bilan qidirib ko'ring.",
                reply_markup=back_kb(),
            )
            return

        await state.clear()
        await message.answer(
            f"🔍 \"{query}\" bo'yicha <b>{len(places)}</b> ta joy topildi:",
            reply_markup=places_list_kb(places),
            parse_mode="HTML",
        )

        reg = is_authenticated(session, message.from_user.id)
        user = get_user_by_telegram(session, message.from_user.id) if reg else None
        for p in places[:3]:
            fav = is_favorite(session, user.id, p.id) if reg and user else False
            await message.answer(
                format_place_short(p),
                reply_markup=place_card_kb(p.id, fav, reg),
                parse_mode="HTML",
            )
    finally:
        session.close()

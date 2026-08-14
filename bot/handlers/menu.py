from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

router = Router()

MENU_BUTTONS = {
    "🔍 Joy qidirish",
    "📋 Barcha joylar",
    "📍 Yaqinimdagi joylar",
    "📚 Yaqin kutubxonalar",
    "🗺 Xarita",
    "⭐ Mashhur joylar",
    "🔧 Filter",
    "🔐 Kirish",
    "🚪 Chiqish",
    "📝 Ro'yxatdan o'tish",
    "👤 Profil",
    "❤️ Sevimlilar",
    "📅 Mening bookinglarim",
    "📩 Adminga xabar",
    "➕ Joy qo'shish",
    "👑 Admin panel",
    "🏠 Bosh menyu",
}


@router.message(F.text.in_(MENU_BUTTONS), ~StateFilter(default_state))
async def menu_escape(message: Message, state: FSMContext):
    """FSM holatida menyu tugmasi bosilganda holatni tozalab, to'g'ri handlerga yo'naltirish."""
    await state.clear()
    text = message.text

    if text == "🔍 Joy qidirish":
        from bot.handlers.search import start_search
        await start_search(message, state)
    elif text == "📋 Barcha joylar":
        from bot.handlers.places import list_all_places
        await list_all_places(message)
    elif text == "📍 Yaqinimdagi joylar":
        from bot.handlers.location import request_nearby_all
        await request_nearby_all(message)
    elif text == "📚 Yaqin kutubxonalar":
        from bot.handlers.location import request_nearby_libraries
        await request_nearby_libraries(message)
    elif text == "🗺 Xarita":
        from bot.handlers.places import map_view
        await map_view(message)
    elif text == "⭐ Mashhur joylar":
        from bot.handlers.places import popular_places
        await popular_places(message)
    elif text == "🔧 Filter":
        from bot.handlers.places import filter_menu
        await filter_menu(message)
    elif text == "📝 Ro'yxatdan o'tish":
        from bot.handlers.auth import start_register
        await start_register(message, state)
    elif text == "🔐 Kirish":
        from bot.handlers.auth import start_login
        await start_login(message, state)
    elif text == "🚪 Chiqish":
        from bot.handlers.auth import do_logout
        await do_logout(message, state)
    elif text == "👤 Profil":
        from bot.handlers.auth import show_profile
        await show_profile(message)
    elif text == "❤️ Sevimlilar":
        from bot.handlers.favorites import list_favorites
        await list_favorites(message)
    elif text == "📅 Mening bookinglarim":
        from bot.handlers.booking import my_bookings
        await my_bookings(message)
    elif text == "📩 Adminga xabar":
        from bot.handlers.contact_admin import start_contact_admin
        await start_contact_admin(message, state)
    elif text == "➕ Joy qo'shish":
        from bot.handlers.add_place import start_add_place
        await start_add_place(message, state)
    elif text == "👑 Admin panel":
        from bot.handlers.admin_panel import open_admin_panel
        await open_admin_panel(message, state)
    elif text == "🏠 Bosh menyu":
        from bot.handlers.start import cmd_help
        await cmd_help(message)

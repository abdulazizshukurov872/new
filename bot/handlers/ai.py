from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import get_session
from bot.keyboards import ai_place_kb, back_kb, guest_menu_kb, main_menu_kb
from bot.services.ai_service import get_ai_recommendations
from bot.states import AIStates

router = Router()


@router.message(F.text == "🤖 AI Yordamchi")
async def start_ai(message: Message, state: FSMContext):
    await state.set_state(AIStates.query)
    await message.answer(
        "🤖 <b>AI Yordamchi</b>\n\n"
        "O'zingizga mos joyni tabiiy til bilan so'rang.\n\n"
        "Misol:\n"
        "<i>Men 3 soat ishlamoqchiman. Tinch, Wi-Fi tez, "
        "rozetkasi bor va 30 000 so'mdan oshmaydigan joy kerak.</i>\n\n"
        "⚠️ AI faqat database'dagi mavjud joylardan tavsiya beradi.",
        parse_mode="HTML",
        reply_markup=back_kb(),
    )


@router.message(AIStates.query)
async def process_ai_query(message: Message, state: FSMContext):
    if message.text == "🏠 Bosh menyu":
        await state.clear()
        from bot.handlers.start import cmd_help
        await cmd_help(message)
        return

    query = message.text.strip()
    wait_msg = await message.answer("🤖 AI tahlil qilmoqda...")

    session = get_session()
    try:
        text, places = await get_ai_recommendations(session, query)
        await state.clear()
        await wait_msg.delete()

        if len(text) > 4000:
            parts = [text[i : i + 4000] for i in range(0, len(text), 4000)]
            for part in parts[:-1]:
                await message.answer(part, parse_mode="HTML")
            await message.answer(parts[-1], reply_markup=ai_place_kb(places), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=ai_place_kb(places), parse_mode="HTML")
    finally:
        session.close()

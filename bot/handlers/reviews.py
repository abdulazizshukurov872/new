from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import Review, get_session
from bot.database.seed import update_place_rating
from bot.keyboards import login_prompt_kb, rating_kb
from bot.services.auth import get_user_by_telegram, is_authenticated
from bot.services.places import get_place
from bot.states import ReviewStates

router = Router()


@router.callback_query(F.data.startswith("review:"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    place_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        if not is_authenticated(session, callback.from_user.id):
            await callback.answer()
            await callback.message.answer(
                "Sharh yozish uchun tizimga kiring:",
                reply_markup=login_prompt_kb(),
            )
            return

        user = get_user_by_telegram(session, callback.from_user.id)

        place = get_place(session, place_id)
        if not place:
            await callback.answer("Joy topilmadi.", show_alert=True)
            return

        await state.set_state(ReviewStates.rating)
        await state.update_data(place_id=place_id)
        await callback.message.answer(
            f"✍️ <b>{place.name}</b> uchun sharh\n\nUmumiy reytingni tanlang:",
            reply_markup=rating_kb("rev_rating"),
            parse_mode="HTML",
        )
    finally:
        session.close()
    await callback.answer()


@router.callback_query(ReviewStates.rating, F.data.startswith("rev_rating:"))
async def review_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewStates.wifi_rating)
    await callback.message.edit_text(
        "📶 Wi-Fi reytingini tanlang:",
        reply_markup=rating_kb("rev_wifi"),
    )
    await callback.answer()


@router.callback_query(ReviewStates.wifi_rating, F.data.startswith("rev_wifi:"))
async def review_wifi(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(wifi_rating=rating)
    await state.set_state(ReviewStates.noise_rating)
    await callback.message.edit_text(
        "🔊 Shovqin reytingini tanlang:",
        reply_markup=rating_kb("rev_noise"),
    )
    await callback.answer()


@router.callback_query(ReviewStates.noise_rating, F.data.startswith("rev_noise:"))
async def review_noise(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(noise_rating=rating)
    await state.set_state(ReviewStates.comfort_rating)
    await callback.message.edit_text(
        "🪑 Qulaylik reytingini tanlang:",
        reply_markup=rating_kb("rev_comfort"),
    )
    await callback.answer()


@router.callback_query(ReviewStates.comfort_rating, F.data.startswith("rev_comfort:"))
async def review_comfort(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split(":")[1])
    await state.update_data(comfort_rating=rating)
    await state.set_state(ReviewStates.comment)
    await callback.message.edit_text("💬 Izohingizni yozing (yoki - deb o'tkazib yuboring):")
    await callback.answer()


@router.message(ReviewStates.comment)
async def review_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if comment == "-":
        comment = ""

    data = await state.get_data()
    session = get_session()
    try:
        user = get_user_by_telegram(session, message.from_user.id)
        review = Review(
            user_id=user.id,
            place_id=data["place_id"],
            rating=data["rating"],
            wifi_rating=data["wifi_rating"],
            noise_rating=data["noise_rating"],
            comfort_rating=data["comfort_rating"],
            comment=comment,
        )
        session.add(review)
        session.commit()
        update_place_rating(data["place_id"])

        await state.clear()
        await message.answer(
            "✅ Sharhingiz qo'shildi! Rahmat.\n\n"
            f"⭐ Umumiy: {data['rating']}/5\n"
            f"📶 Wi-Fi: {data['wifi_rating']}/5\n"
            f"🔊 Shovqin: {data['noise_rating']}/5\n"
            f"🪑 Qulaylik: {data['comfort_rating']}/5",
        )
    finally:
        session.close()

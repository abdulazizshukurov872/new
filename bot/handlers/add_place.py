from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import Place, get_session
from bot.keyboards import place_type_add_kb, yes_no_kb
from bot.services.admin import check_admin
from bot.states import AddPlaceStates

router = Router()


@router.message(F.text == "➕ Joy qo'shish")
async def start_add_place(message: Message, state: FSMContext):
    session = get_session()
    try:
        if not check_admin(session, message.from_user.id, message.from_user.username):
            await message.answer("⛔ Joy qo'shish faqat admin uchun ruxsat etilgan.")
            return
    finally:
        session.close()

    await state.set_state(AddPlaceStates.name)
    await message.answer("➕ <b>Yangi joy qo'shish (Admin)</b>\n\nJoy nomini kiriting:", parse_mode="HTML")


@router.message(AddPlaceStates.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddPlaceStates.description)
    await message.answer("📝 Tavsif kiriting:")


@router.message(AddPlaceStates.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddPlaceStates.type)
    await message.answer("🏷 Joy turini tanlang:", reply_markup=place_type_add_kb())


@router.callback_query(AddPlaceStates.type, F.data.startswith("addtype:"))
async def add_type(callback: CallbackQuery, state: FSMContext):
    ptype = callback.data.split(":")[1]
    await state.update_data(type=ptype)
    await state.set_state(AddPlaceStates.address)
    await callback.message.edit_text("📌 Manzil kiriting:")
    await callback.answer()


@router.message(AddPlaceStates.address)
async def add_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await state.set_state(AddPlaceStates.district)
    await message.answer("🗺 Tuman nomini kiriting (masalan: yunusobod):")


@router.message(AddPlaceStates.district)
async def add_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text.strip().lower())
    await state.set_state(AddPlaceStates.latitude)
    await message.answer("📍 Latitude kiriting (masalan: 41.3111):")


@router.message(AddPlaceStates.latitude)
async def add_latitude(message: Message, state: FSMContext):
    try:
        lat = float(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting:")
        return
    await state.update_data(latitude=lat)
    await state.set_state(AddPlaceStates.longitude)
    await message.answer("📍 Longitude kiriting (masalan: 69.2797):")


@router.message(AddPlaceStates.longitude)
async def add_longitude(message: Message, state: FSMContext):
    try:
        lon = float(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting:")
        return
    await state.update_data(longitude=lon)
    await state.set_state(AddPlaceStates.price)
    await message.answer("💰 Narx (so'm, bepul bo'lsa 0):")


@router.message(AddPlaceStates.price)
async def add_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting:")
        return
    await state.update_data(price=price)
    await state.set_state(AddPlaceStates.wifi_speed)
    await message.answer("📶 Wi-Fi tezligi (Mbps):")


@router.message(AddPlaceStates.wifi_speed)
async def add_wifi(message: Message, state: FSMContext):
    try:
        wifi = int(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting:")
        return
    await state.update_data(wifi_speed=wifi)
    await state.set_state(AddPlaceStates.noise_level)
    await message.answer("🔊 Shovqin darajasi (quiet / moderate / noisy):")


@router.message(AddPlaceStates.noise_level)
async def add_noise(message: Message, state: FSMContext):
    noise = message.text.strip().lower()
    if noise not in ("quiet", "moderate", "noisy"):
        await message.answer("quiet, moderate yoki noisy kiriting:")
        return
    await state.update_data(noise_level=noise)
    await state.set_state(AddPlaceStates.sockets)
    await message.answer("🔌 Rozetka bormi? (ha / yo'q)")


@router.message(AddPlaceStates.sockets)
async def add_sockets(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    sockets = text in ("ha", "yes", "bor", "✅")
    await state.update_data(sockets=sockets)
    await state.set_state(AddPlaceStates.capacity)
    await message.answer("🪑 Umumiy o'rindiqlar soni:")


@router.message(AddPlaceStates.capacity)
async def add_capacity(message: Message, state: FSMContext):
    try:
        capacity = int(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting:")
        return
    await state.update_data(capacity=capacity, available_seats=capacity)
    await state.set_state(AddPlaceStates.working_hours)
    await message.answer("🕐 Ish vaqti (masalan: 09:00-22:00):")


@router.message(AddPlaceStates.working_hours)
async def add_hours(message: Message, state: FSMContext):
    await state.update_data(working_hours=message.text.strip())
    await state.set_state(AddPlaceStates.amenities)
    await message.answer("✨ Qulayliklar (vergul bilan):")


@router.message(AddPlaceStates.amenities)
async def add_amenities(message: Message, state: FSMContext):
    await state.update_data(amenities=message.text.strip())
    data = await state.get_data()

    summary = (
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"📍 {data['name']}\n"
        f"📝 {data['description'][:100]}\n"
        f"🏷 {data['type']}\n"
        f"📌 {data['address']} ({data['district']})\n"
        f"💰 {data['price']} so'm\n"
        f"📶 {data['wifi_speed']} Mbps\n"
        f"🔊 {data['noise_level']}\n"
        f"🪑 {data['capacity']} o'rindiq\n\n"
        f"✅ Admin sifatida joy darhol tasdiqlanadi."
    )

    await state.set_state(AddPlaceStates.confirm)
    await message.answer(summary, reply_markup=yes_no_kb("addplace:yes", "addplace:no"), parse_mode="HTML")


@router.callback_query(AddPlaceStates.confirm, F.data == "addplace:yes")
async def confirm_add_place(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    try:
        from bot.services.auth import get_user_by_telegram

        user = get_user_by_telegram(session, callback.from_user.id)
        place = Place(
            name=data["name"],
            description=data["description"],
            type=data["type"],
            address=data["address"],
            district=data["district"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            price=data["price"],
            wifi_speed=data["wifi_speed"],
            noise_level=data["noise_level"],
            sockets=data["sockets"],
            capacity=data["capacity"],
            available_seats=data["capacity"],
            working_hours=data.get("working_hours", "09:00-22:00"),
            amenities=data.get("amenities", ""),
            created_by=user.id if user else None,
            is_approved=True,
        )
        session.add(place)
        session.commit()

        await state.clear()
        await callback.message.edit_text(
            f"✅ <b>{place.name}</b> muvaffaqiyatli qo'shildi va tasdiqlandi!",
            parse_mode="HTML",
        )
    finally:
        session.close()
    await callback.answer()


@router.callback_query(AddPlaceStates.confirm, F.data == "addplace:no")
async def cancel_add_place(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Joy qo'shish bekor qilindi.")
    await callback.answer()

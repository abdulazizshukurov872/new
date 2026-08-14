from datetime import datetime, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import get_session
from bot.keyboards import booking_cancel_kb, booking_confirm_kb, login_prompt_kb
from bot.services.auth import get_user_by_telegram, is_authenticated
from bot.services.booking import BookingError, cancel_booking, create_booking, format_booking, get_available_seats, get_user_bookings
from bot.services.places import format_place_short, get_place
from bot.states import BookingStates

router = Router()

_pending_bookings: dict[int, dict] = {}


@router.message(F.text == "📅 Mening bookinglarim")
async def my_bookings(message: Message):
    session = get_session()
    try:
        if not is_authenticated(session, message.from_user.id):
            await message.answer(
                "Bookinglarni ko'rish uchun tizimga kiring.",
                reply_markup=login_prompt_kb(),
            )
            return

        user = get_user_by_telegram(session, message.from_user.id)

        bookings = get_user_bookings(session, user.id)
        if not bookings:
            await message.answer("Sizda hali bookinglar yo'q.")
            return

        await message.answer(f"📅 <b>Mening bookinglarim</b> ({len(bookings)} ta):", parse_mode="HTML")
        for b in bookings:
            text = format_booking(b)
            kb = booking_cancel_kb(b.id) if b.status in ("pending", "confirmed") else None
            await message.answer(text, reply_markup=kb)
    finally:
        session.close()


@router.callback_query(F.data.startswith("book:"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    place_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        if not is_authenticated(session, callback.from_user.id):
            await callback.answer()
            await callback.message.answer(
                "📅 Booking qilish uchun avval tizimga kiring:",
                reply_markup=login_prompt_kb(),
            )
            return

        user = get_user_by_telegram(session, callback.from_user.id)

        place = get_place(session, place_id)
        if not place:
            await callback.answer("Joy topilmadi.", show_alert=True)
            return

        if place.available_seats <= 0:
            await callback.answer("Hozir bo'sh joy yo'q.", show_alert=True)
            return

        await state.set_state(BookingStates.date)
        await state.update_data(place_id=place_id)
        await callback.message.answer(
            f"📅 <b>Booking: {place.name}</b>\n\n"
            f"Sana kiriting (DD.MM.YYYY):\n"
            f"Misol: {datetime.now().strftime('%d.%m.%Y')}",
            parse_mode="HTML",
        )
    finally:
        session.close()
    await callback.answer()


@router.message(BookingStates.date)
async def booking_date(message: Message, state: FSMContext):
    try:
        booking_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        if booking_date < datetime.now().date():
            await message.answer("O'tmish sanani tanlab bo'lmaydi. Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Noto'g'ri format. DD.MM.YYYY kiriting:")
        return

    await state.update_data(date=booking_date.isoformat())
    await state.set_state(BookingStates.start_time)
    await message.answer("🕐 Boshlanish vaqtini kiriting (HH:MM):\nMisol: 10:00")


@router.message(BookingStates.start_time)
async def booking_start_time(message: Message, state: FSMContext):
    try:
        start = datetime.strptime(message.text.strip(), "%H:%M").time()
    except ValueError:
        await message.answer("Noto'g'ri format. HH:MM kiriting:")
        return

    await state.update_data(start_time=start.isoformat())
    await state.set_state(BookingStates.end_time)
    await message.answer("🕐 Tugash vaqtini kiriting (HH:MM):\nMisol: 13:00")


@router.message(BookingStates.end_time)
async def booking_end_time(message: Message, state: FSMContext):
    try:
        end = datetime.strptime(message.text.strip(), "%H:%M").time()
    except ValueError:
        await message.answer("Noto'g'ri format. HH:MM kiriting:")
        return

    data = await state.get_data()
    start = time.fromisoformat(data["start_time"])
    if end <= start:
        await message.answer("Tugash vaqti boshlanishdan keyin bo'lishi kerak:")
        return

    place_id = data["place_id"]
    booking_date = datetime.fromisoformat(data["date"]).date()

    session = get_session()
    try:
        place = get_place(session, place_id)
        seats = get_available_seats(session, place, booking_date, start, end)

        if not seats:
            await message.answer("Tanlangan vaqtda bo'sh o'rindiqlar yo'q.")
            await state.clear()
            return

        await state.update_data(end_time=end.isoformat())
        await state.set_state(BookingStates.seat)

        seats_text = ", ".join(str(s) for s in seats[:20])
        await message.answer(
            f"🪑 Bo'sh o'rindiqlar: {seats_text}\n\nO'rindiq raqamini kiriting:"
        )
    finally:
        session.close()


@router.message(BookingStates.seat)
async def booking_seat(message: Message, state: FSMContext):
    try:
        seat = int(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting:")
        return

    data = await state.get_data()
    place_id = data["place_id"]
    booking_date = datetime.fromisoformat(data["date"]).date()
    start = time.fromisoformat(data["start_time"])
    end = time.fromisoformat(data["end_time"])

    session = get_session()
    try:
        place = get_place(session, place_id)
        seats = get_available_seats(session, place, booking_date, start, end)

        if seat not in seats:
            await message.answer(f"Bu o'rindiq band yoki mavjud emas. Bo'sh: {', '.join(map(str, seats[:15]))}")
            return

        summary = (
            f"📋 <b>Booking tasdiqlash</b>\n\n"
            f"{format_place_short(place)}\n\n"
            f"📅 Sana: {booking_date.strftime('%d.%m.%Y')}\n"
            f"🕐 Vaqt: {start.strftime('%H:%M')} — {end.strftime('%H:%M')}\n"
            f"🪑 O'rindiq: {seat}\n\n"
            f"Tasdiqlaysizmi?"
        )

        _pending_bookings[message.from_user.id] = {
            "place_id": place_id,
            "date": booking_date,
            "start": start,
            "end": end,
            "seat": seat,
        }

        await state.clear()
        await message.answer(summary, reply_markup=booking_confirm_kb(place_id), parse_mode="HTML")
    finally:
        session.close()


@router.callback_query(F.data.startswith("bconfirm:"))
async def confirm_booking(callback: CallbackQuery):
    pending = _pending_bookings.get(callback.from_user.id)
    if not pending:
        await callback.answer("Booking ma'lumotlari topilmadi.", show_alert=True)
        return

    session = get_session()
    try:
        user = get_user_by_telegram(session, callback.from_user.id)
        try:
            booking = create_booking(
                session,
                user.id,
                pending["place_id"],
                pending["date"],
                pending["start"],
                pending["end"],
                pending["seat"],
            )
            _pending_bookings.pop(callback.from_user.id, None)
            await callback.message.edit_text(
                f"✅ <b>Booking yaratildi!</b>\n\n{format_booking(booking)}",
                parse_mode="HTML",
            )
        except BookingError as e:
            await callback.message.edit_text(f"❌ {e}")
    finally:
        session.close()
    await callback.answer()


@router.callback_query(F.data == "bcancel")
async def cancel_booking_flow(callback: CallbackQuery):
    _pending_bookings.pop(callback.from_user.id, None)
    await callback.message.edit_text("Booking bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data.startswith("bcancel_id:"))
async def cancel_existing_booking(callback: CallbackQuery):
    booking_id = int(callback.data.split(":")[1])
    session = get_session()
    try:
        user = get_user_by_telegram(session, callback.from_user.id)
        try:
            booking = cancel_booking(session, booking_id, user.id)
            await callback.message.edit_text(
                f"❌ Booking bekor qilindi.\n\n{format_booking(booking)}"
            )
        except BookingError as e:
            await callback.answer(str(e), show_alert=True)
    finally:
        session.close()
    await callback.answer()

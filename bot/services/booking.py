from datetime import date, datetime, time

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from bot.database.models import Booking, Place
from bot.services.places import sync_availability


class BookingError(Exception):
    pass


def get_user_bookings(session: Session, user_id: int) -> list[Booking]:
    from sqlalchemy.orm import joinedload

    return (
        session.query(Booking)
        .options(joinedload(Booking.place))
        .filter(Booking.user_id == user_id)
        .order_by(Booking.date.desc(), Booking.start_time.desc())
        .all()
    )


def get_booking(session: Session, booking_id: int, user_id: int) -> Booking | None:
    return (
        session.query(Booking)
        .filter(Booking.id == booking_id, Booking.user_id == user_id)
        .first()
    )


def get_occupied_seats(
    session: Session, place_id: int, booking_date: date, start: time, end: time
) -> set[int]:
    bookings = (
        session.query(Booking)
        .filter(
            Booking.place_id == place_id,
            Booking.date == booking_date,
            Booking.status.in_(["pending", "confirmed"]),
            or_(
                and_(Booking.start_time < end, Booking.end_time > start),
            ),
        )
        .all()
    )
    return {b.seat_number for b in bookings}


def get_available_seats(
    session: Session, place: Place, booking_date: date, start: time, end: time
) -> list[int]:
    occupied = get_occupied_seats(session, place.id, booking_date, start, end)
    return [i for i in range(1, place.capacity + 1) if i not in occupied]


def create_booking(
    session: Session,
    user_id: int,
    place_id: int,
    booking_date: date,
    start: time,
    end: time,
    seat_number: int,
) -> Booking:
    if start >= end:
        raise BookingError("Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak.")

    place = session.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise BookingError("Joy topilmadi.")

    if not place.is_approved:
        raise BookingError("Bu joy hali tasdiqlanmagan.")

    if seat_number < 1 or seat_number > place.capacity:
        raise BookingError(f"O'rindiq raqami 1 dan {place.capacity} gacha bo'lishi kerak.")

    occupied = get_occupied_seats(session, place_id, booking_date, start, end)
    if seat_number in occupied:
        raise BookingError("Bu o'rindiq tanlangan vaqt oralig'ida band.")

    active_count = len(occupied) + 1
    if active_count > place.capacity:
        raise BookingError("Joy to'liq band.")

    booking = Booking(
        user_id=user_id,
        place_id=place_id,
        date=booking_date,
        start_time=start,
        end_time=end,
        seat_number=seat_number,
        status="confirmed",
    )
    session.add(booking)

    place.available_seats = max(0, place.capacity - active_count)
    sync_availability(session, place_id)

    session.commit()
    session.refresh(booking)
    return booking


def cancel_booking(session: Session, booking_id: int, user_id: int) -> Booking:
    booking = get_booking(session, booking_id, user_id)
    if not booking:
        raise BookingError("Booking topilmadi.")

    if booking.status == "cancelled":
        raise BookingError("Booking allaqachon bekor qilingan.")

    if booking.status == "completed":
        raise BookingError("Yakunlangan bookingni bekor qilib bo'lmaydi.")

    booking.status = "cancelled"

    place = session.query(Place).filter(Place.id == booking.place_id).first()
    if place:
        occupied = get_occupied_seats(
            session, place.id, booking.date, booking.start_time, booking.end_time
        )
        place.available_seats = max(0, place.capacity - len(occupied))
        sync_availability(session, place.id)

    session.commit()
    session.refresh(booking)
    return booking


def format_booking(booking: Booking) -> str:
    from bot.config import BOOKING_STATUS
    from bot.services.places import format_price

    status = BOOKING_STATUS.get(booking.status, booking.status)
    return (
        f"📋 Booking #{booking.id}\n"
        f"📍 {booking.place.name}\n"
        f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
        f"🕐 {booking.start_time.strftime('%H:%M')} — {booking.end_time.strftime('%H:%M')}\n"
        f"🪑 O'rindiq: {booking.seat_number}\n"
        f"💰 Narx: {format_price(booking.place.price)}\n"
        f"📊 Holat: {status}"
    )

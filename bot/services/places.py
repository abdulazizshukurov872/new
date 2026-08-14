from sqlalchemy import or_
from sqlalchemy.orm import Session

from bot.config import AVAILABILITY_STATUS, NOISE_LEVELS, PLACE_TYPES
from bot.database.models import Availability, Booking, Favorite, Place, Review
from bot.services.location import format_distance, haversine_km


def format_price(price: int) -> str:
    if price == 0:
        return "Bepul"
    return f"{price:,} so'm".replace(",", " ")


def format_place_short(place: Place, distance_km: float | None = None) -> str:
    ptype = PLACE_TYPES.get(place.type, place.type)
    noise = NOISE_LEVELS.get(place.noise_level, place.noise_level)
    avail = AVAILABILITY_STATUS.get(
        _availability_status(place.available_seats, place.capacity), "🟢 Bo'sh"
    )
    sockets = "✅ Rozetka bor" if place.sockets else "❌ Rozetka yo'q"
    dist_line = f"📏 Masofa: {format_distance(distance_km)}\n" if distance_km is not None else ""

    return (
        f"📍 <b>{place.name}</b>\n"
        f"{dist_line}"
        f"🏷 {ptype} | ⭐ {place.rating}\n"
        f"📌 {place.address} ({place.district.title()})\n"
        f"📶 Wi-Fi: {place.wifi_speed} Mbps | {noise}\n"
        f"💰 {format_price(place.price)} | {sockets}\n"
        f"🪑 Bo'sh joylar: {place.available_seats}/{place.capacity} | {avail}"
    )


def format_place_detail(place: Place, session: Session) -> str:
    ptype = PLACE_TYPES.get(place.type, place.type)
    noise = NOISE_LEVELS.get(place.noise_level, place.noise_level)
    avail = AVAILABILITY_STATUS.get(
        _availability_status(place.available_seats, place.capacity), "🟢 Bo'sh"
    )
    sockets = "✅ Bor" if place.sockets else "❌ Yo'q"

    reviews = (
        session.query(Review)
        .filter(Review.place_id == place.id)
        .order_by(Review.created_at.desc())
        .limit(3)
        .all()
    )

    text = (
        f"📍 <b>{place.name}</b>\n\n"
        f"📝 {place.description}\n\n"
        f"🏷 Turi: {ptype}\n"
        f"⭐ Reyting: {place.rating}\n"
        f"📌 Manzil: {place.address}\n"
        f"🗺 Tuman: {place.district.title()}\n"
        f"🕐 Ish vaqti: {place.working_hours}\n"
        f"📶 Wi-Fi: {place.wifi_speed} Mbps\n"
        f"🔊 Shovqin: {noise}\n"
        f"🔌 Rozetka: {sockets}\n"
        f"🪑 Sig'im: {place.capacity} | Bo'sh: {place.available_seats} ({avail})\n"
        f"💰 Narx: {format_price(place.price)}\n"
        f"✨ Qulayliklar: {place.amenities}\n"
        f"🗺 Xarita: https://www.openstreetmap.org/?mlat={place.latitude}&mlon={place.longitude}#map=17/{place.latitude}/{place.longitude}"
    )

    if reviews:
        text += "\n\n💬 <b>So'nggi sharhlar:</b>\n"
        for r in reviews:
            text += f"  ⭐ {r.rating}/5 — {r.comment[:80]}{'...' if len(r.comment) > 80 else ''}\n"

    return text


def _availability_status(available: int, total: int) -> str:
    if available <= 0:
        return "full"
    if available <= total * 0.2:
        return "busy"
    return "available"


def search_places(
    session: Session,
    query: str = "",
    district: str = "",
    place_type: str = "",
    noise_level: str = "",
    min_wifi: int = 0,
    has_sockets: bool | None = None,
    max_price: int | None = None,
    free_only: bool = False,
    available_only: bool = False,
    ordering: str = "-rating",
) -> list[Place]:
    q = session.query(Place).filter(Place.is_approved.is_(True))

    if query:
        pattern = f"%{query.lower()}%"
        q = q.filter(
            or_(
                Place.name.ilike(pattern),
                Place.address.ilike(pattern),
                Place.district.ilike(pattern),
                Place.description.ilike(pattern),
            )
        )

    if district:
        q = q.filter(Place.district.ilike(f"%{district.lower()}%"))

    if place_type:
        q = q.filter(Place.type == place_type)

    if noise_level:
        q = q.filter(Place.noise_level == noise_level)

    if min_wifi > 0:
        q = q.filter(Place.wifi_speed >= min_wifi)

    if has_sockets is True:
        q = q.filter(Place.sockets.is_(True))

    if free_only:
        q = q.filter(Place.price == 0)

    if max_price is not None:
        q = q.filter(Place.price <= max_price)

    if available_only:
        q = q.filter(Place.available_seats > 0)

    order_map = {
        "-rating": Place.rating.desc(),
        "rating": Place.rating.asc(),
        "-price": Place.price.desc(),
        "price": Place.price.asc(),
        "-wifi_speed": Place.wifi_speed.desc(),
    }
    q = q.order_by(order_map.get(ordering, Place.rating.desc()))

    return q.all()


def get_place(session: Session, place_id: int) -> Place | None:
    return session.query(Place).filter(Place.id == place_id, Place.is_approved.is_(True)).first()


def get_popular_places(session: Session, limit: int = 5) -> list[Place]:
    return (
        session.query(Place)
        .filter(Place.is_approved.is_(True))
        .order_by(Place.rating.desc())
        .limit(limit)
        .all()
    )


def get_available_places(session: Session, limit: int = 5) -> list[Place]:
    return (
        session.query(Place)
        .filter(Place.is_approved.is_(True), Place.available_seats > 0)
        .order_by(Place.available_seats.desc())
        .limit(limit)
        .all()
    )


def is_favorite(session: Session, user_id: int, place_id: int) -> bool:
    return (
        session.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.place_id == place_id)
        .first()
        is not None
    )


def get_nearby_places(
    session: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    place_type: str = "",
    limit: int = 10,
) -> list[tuple[Place, float]]:
    places = session.query(Place).filter(Place.is_approved.is_(True)).all()
    if place_type:
        places = [p for p in places if p.type == place_type]

    nearby: list[tuple[Place, float]] = []
    for place in places:
        dist = haversine_km(latitude, longitude, place.latitude, place.longitude)
        if dist <= radius_km:
            nearby.append((place, dist))

    nearby.sort(key=lambda x: x[1])
    return nearby[:limit]


def sync_availability(session: Session, place_id: int):
    place = session.query(Place).filter(Place.id == place_id).first()
    if not place:
        return

    avail = session.query(Availability).filter(Availability.place_id == place_id).first()
    status = _availability_status(place.available_seats, place.capacity)

    if avail:
        avail.total_seats = place.capacity
        avail.available_seats = place.available_seats
        avail.occupied_seats = place.capacity - place.available_seats
        avail.status = status
    else:
        session.add(
            Availability(
                place_id=place_id,
                total_seats=place.capacity,
                available_seats=place.available_seats,
                occupied_seats=place.capacity - place.available_seats,
                status=status,
            )
        )

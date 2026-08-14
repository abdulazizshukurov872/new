from bot.database.models import Availability, Place, Review, User, get_session, init_db
from bot.database.real_libraries import REAL_LIBRARIES


def seed_places():
    session = get_session()
    try:
        if session.query(Place).count() > 0:
            return

        sample_places = [
            {
                "name": "Silk Road Coffee",
                "description": "Tinch va zamonaviy kafe. Tez Wi-Fi va ko'p rozetkalar.",
                "type": "cafe",
                "address": "Amir Temur ko'chasi 15",
                "district": "yunusobod",
                "latitude": 41.3675,
                "longitude": 69.2870,
                "price": 25000,
                "working_hours": "08:00-23:00",
                "wifi_speed": 80,
                "noise_level": "quiet",
                "sockets": True,
                "capacity": 35,
                "available_seats": 12,
                "rating": 4.6,
                "amenities": "Wi-Fi, Rozetka, Konditsioner, Kofe",
            },
            {
                "name": "Milliy Kutubxona",
                "description": "Keng o'qish zonalari va bepul Wi-Fi.",
                "type": "library",
                "address": "Navoiy ko'chasi 1",
                "district": "olmazor",
                "latitude": 41.3111,
                "longitude": 69.2797,
                "price": 0,
                "working_hours": "09:00-20:00",
                "wifi_speed": 50,
                "noise_level": "quiet",
                "sockets": True,
                "capacity": 200,
                "available_seats": 85,
                "rating": 4.8,
                "amenities": "Wi-Fi, Rozetka, Suv, O'qish xonalari",
            },
            {
                "name": "WorkHub Coworking",
                "description": "Professional coworking markaz. Meeting roomlar mavjud.",
                "type": "coworking",
                "address": "Shota Rustaveli 45",
                "district": "mirzo ulug'bek",
                "latitude": 41.3385,
                "longitude": 69.3347,
                "price": 45000,
                "working_hours": "24/7",
                "wifi_speed": 150,
                "noise_level": "moderate",
                "sockets": True,
                "capacity": 60,
                "available_seats": 18,
                "rating": 4.7,
                "amenities": "Wi-Fi, Rozetka, Printer, Meeting room, Kofe",
            },
            {
                "name": "Park Zone Free Space",
                "description": "Bog' ichidagi bepul ish zonasi. Tabiiy yorug'lik.",
                "type": "free_zone",
                "address": "Bobur bog'i",
                "district": "yakkasaroy",
                "latitude": 41.2980,
                "longitude": 69.2670,
                "price": 0,
                "working_hours": "07:00-21:00",
                "wifi_speed": 30,
                "noise_level": "moderate",
                "sockets": False,
                "capacity": 40,
                "available_seats": 25,
                "rating": 4.2,
                "amenities": "Wi-Fi, Bog', Skameyka",
            },
            {
                "name": "Study Point Cafe",
                "description": "Talabalar uchun qulay kafe. Tinch muhit.",
                "type": "cafe",
                "address": "Buyuk Ipak yo'li 78",
                "district": "chilonzor",
                "latitude": 41.2850,
                "longitude": 69.2040,
                "price": 20000,
                "working_hours": "07:30-22:30",
                "wifi_speed": 60,
                "noise_level": "quiet",
                "sockets": True,
                "capacity": 45,
                "available_seats": 8,
                "rating": 4.5,
                "amenities": "Wi-Fi, Rozetka, Snack, Konditsioner",
            },
            {
                "name": "TechSpace Hub",
                "description": "IT mutaxassislari uchun coworking. Yuqori tezlikdagi internet.",
                "type": "coworking",
                "address": "Bunyodkor ko'chasi 12",
                "district": "yunusobod",
                "latitude": 41.3720,
                "longitude": 69.2950,
                "price": 55000,
                "working_hours": "08:00-22:00",
                "wifi_speed": 200,
                "noise_level": "quiet",
                "sockets": True,
                "capacity": 50,
                "available_seats": 15,
                "rating": 4.9,
                "amenities": "Wi-Fi, Rozetka, Monitor, Kofe, Parking",
            },
            {
                "name": "Central Library",
                "description": "Markaziy kutubxona. Sessiya davrida ham ochiq.",
                "type": "library",
                "address": "Alisher Navoiy ko'chasi 1",
                "district": "shayxontohur",
                "latitude": 41.3190,
                "longitude": 69.2400,
                "price": 0,
                "working_hours": "09:00-18:00",
                "wifi_speed": 40,
                "noise_level": "quiet",
                "sockets": True,
                "capacity": 150,
                "available_seats": 60,
                "rating": 4.4,
                "amenities": "Wi-Fi, Rozetka, Suv, Kutubxona resurslari",
            },
            {
                "name": "Green Bean Coffee",
                "description": "Yashil muhitdagi kafe. Tinch va qulay.",
                "type": "cafe",
                "address": "Osiyo ko'chasi 22",
                "district": "mirabad",
                "latitude": 41.3050,
                "longitude": 69.2780,
                "price": 30000,
                "working_hours": "08:00-00:00",
                "wifi_speed": 70,
                "noise_level": "moderate",
                "sockets": True,
                "capacity": 30,
                "available_seats": 5,
                "rating": 4.3,
                "amenities": "Wi-Fi, Rozetka, Kofe, Desert",
            },
        ]

        for data in sample_places:
            place = Place(**data)
            session.add(place)
            session.flush()

            avail = _calc_availability(place.available_seats, place.capacity)
            session.add(
                Availability(
                    place_id=place.id,
                    total_seats=place.capacity,
                    available_seats=place.available_seats,
                    occupied_seats=place.capacity - place.available_seats,
                    status=avail,
                )
            )

        session.commit()
    finally:
        session.close()


def _calc_availability(available: int, total: int) -> str:
    if available <= 0:
        return "full"
    if available <= total * 0.2:
        return "busy"
    return "available"


def seed_real_libraries():
    """Haqiqiy kutubxonalarni bazaga qo'shish yoki yangilash."""
    session = get_session()
    try:
        for data in REAL_LIBRARIES:
            existing = session.query(Place).filter(Place.name == data["name"]).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                existing.is_approved = True
                place = existing
            else:
                place = Place(**data, is_approved=True)
                session.add(place)
                session.flush()

            avail = session.query(Availability).filter(Availability.place_id == place.id).first()
            status = _calc_availability(place.available_seats, place.capacity)
            if avail:
                avail.total_seats = place.capacity
                avail.available_seats = place.available_seats
                avail.occupied_seats = place.capacity - place.available_seats
                avail.status = status
            else:
                session.add(
                    Availability(
                        place_id=place.id,
                        total_seats=place.capacity,
                        available_seats=place.available_seats,
                        occupied_seats=place.capacity - place.available_seats,
                        status=status,
                    )
                )

        session.commit()
    finally:
        session.close()


def update_place_rating(place_id: int):
    session = get_session()
    try:
        place = session.query(Place).filter(Place.id == place_id).first()
        if not place:
            return

        reviews = session.query(Review).filter(Review.place_id == place_id).all()
        if not reviews:
            return

        avg = sum(r.rating for r in reviews) / len(reviews)
        place.rating = round(avg, 1)
        session.commit()
    finally:
        session.close()

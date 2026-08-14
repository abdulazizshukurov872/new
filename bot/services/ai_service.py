import json
import re

from openai import OpenAI
from sqlalchemy.orm import Session

from bot.config import OPENAI_API_KEY
from bot.services.places import format_place_short, search_places


def parse_natural_query(text: str) -> dict:
    """Rule-based fallback parser for Uzbek/Russian/English queries."""
    params: dict = {}
    lower = text.lower()

    districts = [
        "yunusobod", "chilonzor", "mirzo ulug'bek", "olmazor",
        "yakkasaroy", "mirabad", "shayxontohur", "sergeli",
        "uchtepa", "bektemir", "yashnobod",
    ]
    for d in districts:
        if d in lower:
            params["district"] = d
            break

    if any(w in lower for w in ["kafe", "cafe", "кофе"]):
        params["place_type"] = "cafe"
    elif any(w in lower for w in ["kutubxona", "library", "библиотека"]):
        params["place_type"] = "library"
    elif any(w in lower for w in ["coworking", "коворкинг"]):
        params["place_type"] = "coworking"
    elif any(w in lower for w in ["bepul", "free", "бесплат"]):
        params["free_only"] = True

    if any(w in lower for w in ["tinch", "quiet", "тиш"]):
        params["noise_level"] = "quiet"

    if any(w in lower for w in ["rozetka", "socket", "розетка"]):
        params["has_sockets"] = True

    wifi_match = re.search(r"(\d+)\s*(mbps|мбит|mb)", lower)
    if wifi_match:
        params["min_wifi"] = int(wifi_match.group(1))
    elif any(w in lower for w in ["tez wifi", "fast wifi", "быстрый"]):
        params["min_wifi"] = 50

    price_match = re.search(r"(\d[\d\s]*)\s*(so'm|sum|сум)", lower)
    if price_match:
        params["max_price"] = int(price_match.group(1).replace(" ", ""))

    return params


async def get_ai_recommendations(session: Session, user_query: str) -> tuple[str, list]:
    places_data = search_places(session, available_only=True)
    if not places_data:
        return "Hozircha mavjud joylar topilmadi.", []

    places_json = [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "district": p.district,
            "address": p.address,
            "price": p.price,
            "wifi_speed": p.wifi_speed,
            "noise_level": p.noise_level,
            "sockets": p.sockets,
            "available_seats": p.available_seats,
            "capacity": p.capacity,
            "rating": p.rating,
            "amenities": p.amenities,
        }
        for p in places_data
    ]

    if OPENAI_API_KEY:
        try:
            return await _openai_recommend(user_query, places_json)
        except Exception:
            pass

    return _rule_based_recommend(session, user_query, places_json)


async def _openai_recommend(user_query: str, places_json: list) -> tuple[str, list]:
    client = OpenAI(api_key=OPENAI_API_KEY)

    system_prompt = (
        "Siz QuietSpace Tashkent AI yordamchisisiz. "
        "Faqat berilgan database'dagi joylardan tavsiya bering. "
        "Mavjud bo'lmagan joy yoki ma'lumotni o'ylab topmang. "
        "Javobni o'zbek tilida bering. "
        "JSON formatda javob qaytaring: "
        '{"explanation": "...", "place_ids": [1, 2, 3], "reasons": {"1": "sabab", ...}}'
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"So'rov: {user_query}\n\nMavjud joylar:\n{json.dumps(places_json, ensure_ascii=False)}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    result = json.loads(response.choices[0].message.content)
    place_ids = result.get("place_ids", [])
    reasons = result.get("reasons", {})
    explanation = result.get("explanation", "")

    id_set = {p["id"] for p in places_json}
    valid_ids = [pid for pid in place_ids if pid in id_set][:5]

    from bot.database.models import get_session
    from bot.services.places import get_place

    db = get_session()
    try:
        places = [get_place(db, pid) for pid in valid_ids]
        places = [p for p in places if p]

        text = f"🤖 <b>AI Tavsiyalar</b>\n\n{explanation}\n\n"
        for p in places:
            reason = reasons.get(str(p.id), reasons.get(p.id, ""))
            text += format_place_short(p)
            if reason:
                text += f"\n💡 <i>Nima uchun mos: {reason}</i>"
            text += "\n\n─────────────\n\n"

        return text.strip(), places
    finally:
        db.close()


def _rule_based_recommend(session: Session, user_query: str, places_json: list) -> tuple[str, list]:
    params = parse_natural_query(user_query)
    places = search_places(session, **params, available_only=True)

    if not params.get("max_price") and "30000" in user_query.replace(" ", ""):
        places = [p for p in places if p.price <= 30000]

    places = places[:5]

    if not places:
        places = search_places(session, available_only=True)[:3]

    text = (
        "🤖 <b>AI Tavsiyalar</b> (database asosida)\n\n"
        f"So'rovingiz: <i>{user_query}</i>\n\n"
    )

    for p in places:
        reasons = []
        if params.get("noise_level") == "quiet" and p.noise_level == "quiet":
            reasons.append("tinch muhit")
        if params.get("min_wifi") and p.wifi_speed >= params.get("min_wifi", 0):
            reasons.append(f"Wi-Fi {p.wifi_speed} Mbps")
        if params.get("has_sockets") and p.sockets:
            reasons.append("rozetka bor")
        if params.get("max_price") and p.price <= params["max_price"]:
            reasons.append(f"narx {p.price} so'm")
        if params.get("district") and params["district"] in p.district.lower():
            reasons.append(f"{p.district.title()} tumani")

        text += format_place_short(p)
        if reasons:
            text += f"\n💡 <i>Mosligi: {', '.join(reasons)}</i>"
        text += "\n\n─────────────\n\n"

    return text.strip(), places

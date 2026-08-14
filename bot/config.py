import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'quietspace.db'}")


def _parse_int_list(value: str) -> list[int]:
    items = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            items.append(int(part))
    return items


def _parse_str_list(value: str) -> list[str]:
    return [p.strip().lstrip("@").lower() for p in value.split(",") if p.strip()]


# Bir nechta admin: vergul bilan ajrating
# Masalan: ADMIN_TELEGRAM_IDS=5966552045,8438959127
ADMIN_TELEGRAM_IDS = _parse_int_list(
    os.getenv(
        "ADMIN_TELEGRAM_IDS",
        os.getenv("ADMIN_TELEGRAM_ID", "5966552045"),
    )
)
ADMIN_USERNAMES = _parse_str_list(
    os.getenv(
        "ADMIN_USERNAMES",
        os.getenv("ADMIN_USERNAME", "Abdulaziz6121"),
    )
)

# Asosiy admin (xabarlar shu yerga ham boradi)
ADMIN_TELEGRAM_ID = ADMIN_TELEGRAM_IDS[0] if ADMIN_TELEGRAM_IDS else 5966552045
ADMIN_USERNAME = ADMIN_USERNAMES[0] if ADMIN_USERNAMES else "Abdulaziz6121"

PLACE_TYPES = {
    "cafe": "☕ Kafe",
    "library": "📚 Kutubxona",
    "coworking": "🏢 Coworking",
    "free_zone": "🆓 Bepul zona",
}

NOISE_LEVELS = {
    "quiet": "🔇 Tinch",
    "moderate": "🔉 O'rtacha",
    "noisy": "🔊 Shovqinli",
}

AVAILABILITY_STATUS = {
    "available": "🟢 Bo'sh",
    "busy": "🟡 Kam joy",
    "full": "🔴 To'liq",
}

BOOKING_STATUS = {
    "pending": "⏳ Kutilmoqda",
    "confirmed": "✅ Tasdiqlangan",
    "cancelled": "❌ Bekor qilingan",
    "completed": "✔️ Yakunlangan",
}

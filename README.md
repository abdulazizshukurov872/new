# QuietSpace Tashkent — Telegram Bot

Toshkentda tinch ishlash joylarini topish, solishtirish, AI tavsiya olish va bron qilish uchun Telegram bot.

## Imkoniyatlar

### Mehmon (ro'yxatdan o'tmasdan)
- Joylarni ko'rish va qidirish
- Filter (turi, Wi-Fi, shovqin, narx, bo'sh joy)
- Xarita havolalari (OpenStreetMap)
- AI yordamchi (database asosida tavsiya)
- Mashhur joylar

### Ro'yxatdan o'tgan foydalanuvchi
- Booking qilish (sana, vaqt, o'rindiq)
- Bookinglarni ko'rish va bekor qilish
- Sharh va reyting qoldirish
- Sevimlilar
- Yangi joy qo'shish (admin tasdiqlashidan keyin)

## O'rnatish

### 1. Telegram Bot Token olish

1. [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username bering
4. Tokenni nusxalang

### 2. Loyihani sozlash

```bash
cd quietspace-bot
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
```

`.env` faylini tahrirlang:

```
BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here   # ixtiyoriy
DATABASE_URL=sqlite:///./quietspace.db
```

> `OPENAI_API_KEY` ixtiyoriy. Berilmasa, AI rule-based parser orqali ishlaydi.

### 3. Botni ishga tushirish

```bash
python run.py
```

## Bot buyruqlari va tugmalar

| Tugma | Tavsif |
|-------|--------|
| 🔍 Joy qidirish | Nom, tuman, manzil bo'yicha qidiruv |
| 📋 Barcha joylar | Barcha tasdiqlangan joylar |
| 🗺 Xarita | OpenStreetMap havolalari |
| 🤖 AI Yordamchi | Tabiiy til orqali tavsiya |
| ⭐ Mashhur joylar | Eng yuqori reytingli joylar |
| 🔧 Filter | Turi, Wi-Fi, shovqin, narx |
| 📝 Ro'yxatdan o'tish | Email bilan ro'yxatdan o'tish |
| 📅 Mening bookinglarim | Bookinglar tarixi |
| ❤️ Sevimlilar | Saqlangan joylar |
| ➕ Joy qo'shish | Yangi joy taklif qilish |

## Arxitektura

```
quietspace-bot/
├── bot/
│   ├── config.py          # Sozlamalar
│   ├── keyboards.py       # Tugmalar
│   ├── states.py          # FSM holatlar
│   ├── database/
│   │   ├── models.py      # SQLAlchemy modellar
│   │   └── seed.py        # Namuna ma'lumotlar
│   ├── services/
│   │   ├── places.py      # Joy qidiruv/filter
│   │   ├── booking.py     # Booking logikasi
│   │   ├── auth.py        # Autentifikatsiya
│   │   └── ai_service.py  # AI tavsiyalar
│   └── handlers/          # Telegram handlerlar
├── run.py                 # Ishga tushirish
├── requirements.txt
└── .env.example
```

## TZ talablariga moslik

| Talab | Holat |
|-------|-------|
| Guest registration qilmasdan joylarni ko'radi | ✅ |
| Search va filter | ✅ |
| Xarita | ✅ (OpenStreetMap havolalari) |
| Place Details | ✅ |
| AI database asosida tavsiya | ✅ |
| Booking uchun auth | ✅ |
| Seat availability tekshiruvi | ✅ |
| Review va rating | ✅ |
| Favorites | ✅ |
| Joy qo'shish (pending → admin) | ✅ |
| JWT | ➖ Telegram auth (TZ web API uchun) |

## Keyingi bosqich

- Django REST API bilan integratsiya (`/api/` endpointlar)
- PostgreSQL ga o'tish
- Admin panel (Django Admin)
- Push notificationlar

## Texnologiyalar

- Python 3.11+
- aiogram 3.x
- SQLAlchemy + SQLite
- OpenAI API (ixtiyoriy)

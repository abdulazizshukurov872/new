from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.config import NOISE_LEVELS, PLACE_TYPES


def get_menu_kb(logged_in: bool, admin: bool = False) -> ReplyKeyboardMarkup:
    if logged_in and admin:
        return admin_menu_kb()
    if logged_in:
        return main_menu_kb()
    return guest_menu_kb()


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Joy qidirish"), KeyboardButton(text="📋 Barcha joylar")],
            [KeyboardButton(text="📍 Yaqinimdagi joylar"), KeyboardButton(text="📚 Yaqin kutubxonalar")],
            [KeyboardButton(text="🗺 Xarita"), KeyboardButton(text="⭐ Mashhur joylar")],
            [KeyboardButton(text="🔧 Filter"), KeyboardButton(text="👤 Profil")],
            [KeyboardButton(text="❤️ Sevimlilar"), KeyboardButton(text="📅 Mening bookinglarim")],
            [KeyboardButton(text="📩 Adminga xabar"), KeyboardButton(text="🚪 Chiqish")],
        ],
        resize_keyboard=True,
    )


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Joy qidirish"), KeyboardButton(text="📋 Barcha joylar")],
            [KeyboardButton(text="📍 Yaqinimdagi joylar"), KeyboardButton(text="📚 Yaqin kutubxonalar")],
            [KeyboardButton(text="🗺 Xarita"), KeyboardButton(text="⭐ Mashhur joylar")],
            [KeyboardButton(text="➕ Joy qo'shish"), KeyboardButton(text="👑 Admin panel")],
            [KeyboardButton(text="👤 Profil"), KeyboardButton(text="🚪 Chiqish")],
            [KeyboardButton(text="❤️ Sevimlilar"), KeyboardButton(text="📅 Mening bookinglarim")],
        ],
        resize_keyboard=True,
    )


def guest_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Joy qidirish"), KeyboardButton(text="📋 Barcha joylar")],
            [KeyboardButton(text="📍 Yaqinimdagi joylar"), KeyboardButton(text="📚 Yaqin kutubxonalar")],
            [KeyboardButton(text="🗺 Xarita"), KeyboardButton(text="⭐ Mashhur joylar")],
            [KeyboardButton(text="🔧 Filter"), KeyboardButton(text="📩 Adminga xabar")],
            [KeyboardButton(text="🔐 Kirish"), KeyboardButton(text="📝 Ro'yxatdan o'tish")],
        ],
        resize_keyboard=True,
    )


def location_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📌 Lokatsiyamni yuborish", request_location=True)],
            [KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Bosh menyu")]],
        resize_keyboard=True,
    )


def place_card_kb(place_id: int, is_fav: bool = False, is_registered: bool = False) -> InlineKeyboardMarkup:
    fav_text = "💔 Olib tashlash" if is_fav else "❤️ Saqlash"
    rows = [
        [
            InlineKeyboardButton(text="📖 Batafsil", callback_data=f"place:{place_id}"),
            InlineKeyboardButton(text="📅 Bron qilish", callback_data=f"book:{place_id}"),
        ],
    ]
    if is_registered:
        rows.append([
            InlineKeyboardButton(text=fav_text, callback_data=f"fav:{place_id}"),
            InlineKeyboardButton(text="✍️ Sharh yozish", callback_data=f"review:{place_id}"),
        ])
    rows.append([
        InlineKeyboardButton(text="🗺 Xaritada", callback_data=f"map:{place_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def place_detail_kb(place_id: int, is_fav: bool = False, is_registered: bool = False) -> InlineKeyboardMarkup:
    fav_text = "💔 Sevimlilardan olib tashlash" if is_fav else "❤️ Sevimlilarga qo'shish"
    rows = [
        [InlineKeyboardButton(text="📅 Bron qilish", callback_data=f"book:{place_id}")],
    ]
    if is_registered:
        rows.append([
            InlineKeyboardButton(text=fav_text, callback_data=f"fav:{place_id}"),
            InlineKeyboardButton(text="✍️ Sharh yozish", callback_data=f"review:{place_id}"),
        ])
    rows.append([
        InlineKeyboardButton(text="🗺 Xaritada ochish", callback_data=f"map:{place_id}"),
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="places:list"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def places_list_kb(places: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    start = page * per_page
    end = start + per_page
    page_places = places[start:end]

    rows = []
    for p in page_places:
        rows.append([
            InlineKeyboardButton(
                text=f"📍 {p.name} ⭐{p.rating}",
                callback_data=f"place:{p.id}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"page:{page - 1}"))
    if end < len(places):
        nav.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"page:{page + 1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def filter_type_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"ftype:{key}")] for key, label in PLACE_TYPES.items()]
    rows.append([InlineKeyboardButton(text="🔄 Barchasi", callback_data="ftype:all")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="filter:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filter_noise_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"noise:{key}")] for key, label in NOISE_LEVELS.items()]
    rows.append([InlineKeyboardButton(text="🔄 Barchasi", callback_data="noise:all")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="filter:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filter_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏷 Joy turi", callback_data="filter:type")],
            [InlineKeyboardButton(text="🔊 Shovqin darajasi", callback_data="filter:noise")],
            [InlineKeyboardButton(text="📶 Wi-Fi 50+ Mbps", callback_data="filter:wifi50")],
            [InlineKeyboardButton(text="🔌 Rozetka bor", callback_data="filter:sockets")],
            [InlineKeyboardButton(text="🆓 Bepul joylar", callback_data="filter:free")],
            [InlineKeyboardButton(text="🟢 Bo'sh joy bor", callback_data="filter:available")],
            [InlineKeyboardButton(text="🔄 Filterni tozalash", callback_data="filter:clear")],
        ]
    )


def rating_kb(prefix: str = "rate") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 1", callback_data=f"{prefix}:1"),
                InlineKeyboardButton(text="⭐ 2", callback_data=f"{prefix}:2"),
                InlineKeyboardButton(text="⭐ 3", callback_data=f"{prefix}:3"),
                InlineKeyboardButton(text="⭐ 4", callback_data=f"{prefix}:4"),
                InlineKeyboardButton(text="⭐ 5", callback_data=f"{prefix}:5"),
            ]
        ]
    )


def booking_confirm_kb(place_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"bconfirm:{place_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bcancel"),
            ]
        ]
    )


def booking_cancel_kb(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bookingni bekor qilish", callback_data=f"bcancel_id:{booking_id}")]
        ]
    )


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Chiqish", callback_data="logout:confirm")],
        ]
    )


def login_prompt_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Kirish", callback_data="login:start")],
            [InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="register:start")],
        ]
    )


def register_prompt_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="register:start")],
        ]
    )


def yes_no_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=yes_data),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=no_data),
            ]
        ]
    )


def place_type_add_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"addtype:{key}")] for key, label in PLACE_TYPES.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
            [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="adm:users")],
            [InlineKeyboardButton(text="🔄 Rol o'zgartirish", callback_data="adm:role")],
            [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="adm:broadcast")],
            [InlineKeyboardButton(text="◀️ Yopish", callback_data="adm:close")],
        ]
    )


def users_manage_kb(users: list) -> InlineKeyboardMarkup:
    rows = []
    for user in users:
        if user.role == "admin":
            rows.append([
                InlineKeyboardButton(
                    text=f"👑 {user.name} (admin)",
                    callback_data=f"adm:userinfo:{user.telegram_id}",
                )
            ])
        elif user.is_active:
            rows.append([
                InlineKeyboardButton(
                    text=f"✅ {user.name}",
                    callback_data=f"adm:userinfo:{user.telegram_id}",
                ),
                InlineKeyboardButton(
                    text="🚫 Bloklash",
                    callback_data=f"adm:blockid:{user.telegram_id}",
                ),
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    text=f"🚫 {user.name}",
                    callback_data=f"adm:userinfo:{user.telegram_id}",
                ),
                InlineKeyboardButton(
                    text="✅ Chiqarish",
                    callback_data=f"adm:unblockid:{user.telegram_id}",
                ),
            ])
    rows.append([InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm:users")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_actions_kb(user) -> InlineKeyboardMarkup:
    rows = []
    if user.role != "admin":
        if user.is_active:
            rows.append([
                InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm:blockid:{user.telegram_id}")
            ])
        else:
            rows.append([
                InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"adm:unblockid:{user.telegram_id}")
            ])
        rows.append([
            InlineKeyboardButton(text="👤 User", callback_data=f"adm:setrole:{user.telegram_id}:user"),
            InlineKeyboardButton(text="👑 Admin", callback_data=f"adm:setrole:{user.telegram_id}:admin"),
        ])
    rows.append([InlineKeyboardButton(text="◀️ Ro'yxatga", callback_data="adm:users")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def contact_admin_block_kb(telegram_id: int, is_blocked: bool = False) -> InlineKeyboardMarkup:
    if is_blocked:
        btn = InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"adm:unblockid:{telegram_id}")
    else:
        btn = InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm:blockid:{telegram_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


def role_select_kb(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 User", callback_data=f"adm:setrole:{telegram_id}:user"),
                InlineKeyboardButton(text="👑 Admin", callback_data=f"adm:setrole:{telegram_id}:admin"),
            ],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:back")],
        ]
    )


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="adm:bsend"),
                InlineKeyboardButton(text="❌ Bekor", callback_data="adm:bcancel"),
            ]
        ]
    )


def ai_place_kb(places: list) -> InlineKeyboardMarkup:
    rows = []
    for p in places[:5]:
        rows.append([
            InlineKeyboardButton(text=f"📍 {p.name}", callback_data=f"place:{p.id}"),
            InlineKeyboardButton(text="📅 Bron", callback_data=f"book:{p.id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

from sqlalchemy.orm import Session

from bot.config import ADMIN_TELEGRAM_IDS, ADMIN_USERNAMES
from bot.database.models import Booking, Favorite, Place, Review, User
from bot.services.session import mark_logged_out


def is_admin(telegram_id: int, username: str | None = None) -> bool:
    if telegram_id in ADMIN_TELEGRAM_IDS:
        return True
    if username and username.lstrip("@").lower() in ADMIN_USERNAMES:
        return True
    return False


def is_admin_user(user: User | None) -> bool:
    return user is not None and user.role == "admin"


def check_admin(session: Session, telegram_id: int, username: str | None = None) -> bool:
    if is_admin(telegram_id, username):
        return True
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    return is_admin_user(user)


def is_blocked(session: Session, telegram_id: int, username: str | None = None) -> bool:
    if check_admin(session, telegram_id, username):
        return False
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    return user is not None and not user.is_active


def setup_admins(session: Session) -> None:
    for telegram_id in ADMIN_TELEGRAM_IDS:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.role = "admin"
            user.is_active = True
    session.commit()


def promote_if_admin(session: Session, telegram_id: int, username: str | None = None) -> None:
    if not is_admin(telegram_id, username):
        return
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.role = "admin"
        user.is_active = True
        session.commit()


def get_admin_telegram_ids(session: Session) -> list[int]:
    ids = set(ADMIN_TELEGRAM_IDS)
    admins = session.query(User).filter(User.role == "admin").all()
    for user in admins:
        ids.add(user.telegram_id)
    return list(ids)


def find_user(session: Session, query: str) -> User | None:
    query = query.strip()
    if query.isdigit():
        return session.query(User).filter(User.telegram_id == int(query)).first()
    if "@" in query:
        return session.query(User).filter(User.email == query.lower()).first()
    return session.query(User).filter(User.email == query.lower()).first()


def set_user_role(session: Session, user: User, role: str) -> User:
    if role not in ("user", "admin"):
        raise ValueError("Rol faqat user yoki admin bo'lishi kerak.")
    if user.telegram_id in ADMIN_TELEGRAM_IDS and role != "admin":
        raise ValueError("Asosiy admin rolini o'zgartirib bo'lmaydi.")
    user.role = role
    session.commit()
    session.refresh(user)
    return user


def block_user(session: Session, user: User) -> User:
    if check_admin(session, user.telegram_id):
        raise ValueError("Adminni bloklab bo'lmaydi.")
    user.is_active = False
    user.is_session_active = False
    session.commit()
    mark_logged_out(user.telegram_id)
    session.refresh(user)
    return user


def unblock_user(session: Session, user: User) -> User:
    user.is_active = True
    session.commit()
    session.refresh(user)
    return user


def get_stats(session: Session) -> dict:
    return {
        "users": session.query(User).count(),
        "active_users": session.query(User).filter(User.is_active.is_(True)).count(),
        "blocked_users": session.query(User).filter(User.is_active.is_(False)).count(),
        "admins": session.query(User).filter(User.role == "admin").count(),
        "places": session.query(Place).count(),
        "bookings": session.query(Booking).count(),
        "reviews": session.query(Review).count(),
        "favorites": session.query(Favorite).count(),
    }


def get_recent_users(session: Session, limit: int = 20) -> list[User]:
    return session.query(User).order_by(User.created_at.desc()).limit(limit).all()


def get_all_users(session: Session) -> list[User]:
    return session.query(User).order_by(User.created_at.desc()).all()


def get_broadcast_users(session: Session) -> list[User]:
    return session.query(User).filter(User.is_active.is_(True)).all()


setup_admin = setup_admins

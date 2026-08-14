import hashlib
import secrets

from sqlalchemy.orm import Session

from bot.database.models import User
from bot.services.session import mark_logged_in, mark_logged_out


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, expected = stored.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return secrets.compare_digest(digest.hex(), expected)


def _activate_session(session: Session, user: User, telegram_id: int) -> User:
    user.telegram_id = telegram_id
    user.is_session_active = True
    session.commit()
    session.refresh(user)
    mark_logged_in(telegram_id)
    return user


def register_user(session: Session, telegram_id: int, name: str, email: str, password: str) -> User:
    email = email.strip().lower()
    existing_email = session.query(User).filter(User.email == email).first()

    if existing_email:
        if existing_email.password_hash:
            raise ValueError("Bu email allaqachon ro'yxatdan o'tgan. Login qiling.")
        existing_email.name = name
        existing_email.password_hash = hash_password(password)
        return _activate_session(session, existing_email, telegram_id)

    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.name = name
        user.email = email
        user.password_hash = hash_password(password)
        return _activate_session(session, user, telegram_id)

    user = User(
        telegram_id=telegram_id,
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_session_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    mark_logged_in(telegram_id)
    return user


def login_user(session: Session, telegram_id: int, email: str, password: str) -> User:
    email = email.strip().lower()
    user = session.query(User).filter(User.email == email).first()

    if not user:
        raise ValueError("Email topilmadi. Avval ro'yxatdan o'ting.")

    if not user.password_hash:
        raise ValueError("Parol o'rnatilmagan. Qayta ro'yxatdan o'ting.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Noto'g'ri parol.")

    if not user.is_active:
        raise ValueError("Hisobingiz bloklangan.")

    return _activate_session(session, user, telegram_id)


def logout_user(session: Session, telegram_id: int) -> bool:
    user = get_user_by_telegram(session, telegram_id)
    was_active = bool(user and user.is_session_active)
    if user:
        user.is_session_active = False
        session.commit()
    mark_logged_out(telegram_id)
    return was_active


def get_user_by_telegram(session: Session, telegram_id: int) -> User | None:
    return session.query(User).filter(User.telegram_id == telegram_id).first()


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email.strip().lower()).first()


def is_authenticated(session: Session, telegram_id: int) -> bool:
    user = get_user_by_telegram(session, telegram_id)
    if user is None or not user.email or not user.password_hash:
        return False
    if user.is_session_active:
        mark_logged_in(telegram_id)
        return True
    return False


def is_registered(user: User | None) -> bool:
    return user is not None and user.email is not None and user.password_hash is not None

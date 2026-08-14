from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from bot.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    is_session_active = Column(Boolean, default=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    places_created = relationship("Place", back_populates="created_by_user")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    type = Column(String(50), nullable=False)
    address = Column(String(300), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    price = Column(Integer, default=0)
    working_hours = Column(String(100), default="09:00-22:00")
    wifi_speed = Column(Integer, default=0)
    noise_level = Column(String(20), default="moderate")
    sockets = Column(Boolean, default=True)
    capacity = Column(Integer, default=20)
    available_seats = Column(Integer, default=20)
    rating = Column(Float, default=0.0)
    amenities = Column(Text, default="")
    image_url = Column(String(500), default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_user = relationship("User", back_populates="places_created")
    reviews = relationship("Review", back_populates="place")
    bookings = relationship("Booking", back_populates="place")
    favorites = relationship("Favorite", back_populates="place")
    availability = relationship("Availability", back_populates="place", uselist=False)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    wifi_rating = Column(Integer, nullable=False)
    noise_rating = Column(Integer, nullable=False)
    comfort_rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    place = relationship("Place", back_populates="reviews")


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True)
    place_id = Column(Integer, ForeignKey("places.id"), unique=True, nullable=False)
    total_seats = Column(Integer, default=20)
    available_seats = Column(Integer, default=20)
    occupied_seats = Column(Integer, default=0)
    status = Column(String(20), default="available")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    place = relationship("Place", back_populates="availability")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    seat_number = Column(Integer, nullable=False)
    status = Column(String(20), default="confirmed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    place = relationship("Place", back_populates="bookings")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "place_id", name="uq_user_place_favorite"),)

    user = relationship("User", back_populates="favorites")
    place = relationship("Place", back_populates="favorites")


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_users_table()


def _migrate_users_table():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    def _add_column(name: str, ddl: str):
        cols = {col["name"] for col in inspect(engine).get_columns("users")}
        if name not in cols:
            with engine.begin() as conn:
                conn.execute(text(ddl))

    _add_column("password_hash", "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
    _add_column("is_session_active", "ALTER TABLE users ADD COLUMN is_session_active BOOLEAN DEFAULT 0")


def get_session():
    return SessionLocal()

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import enum

DATABASE_URL = "sqlite:///./reservations.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ResourceType(str, enum.Enum):
    TABLE = "table"
    ESPACE = "espace"

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NOSHOW = "noshow"
    COMPLETED = "completed"

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    resource_type = Column(Enum(ResourceType), default=ResourceType.TABLE)
    deposit_amount_cents = Column(Integer)
    currency = Column(String, default="eur")
    max_capacity = Column(Integer)
    bookings = relationship("Booking", back_populates="restaurant")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    client_name = Column(String)
    client_email = Column(String)
    pax = Column(Integer)
    stripe_payment_intent_id = Column(String, unique=True, nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    restaurant = relationship("Restaurant", back_populates="bookings")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

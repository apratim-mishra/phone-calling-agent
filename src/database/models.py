from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from src.database import Base


class CallDirection(enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"
    CANCELED = "canceled"


class Property(Base):
    """Real estate property for semantic search."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[float] = mapped_column(Float, nullable=False)
    square_feet: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "square_feet": self.square_feet,
            "location": self.location,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
        }

    def to_search_text(self) -> str:
        """Generate text for embedding."""
        return (
            f"{self.title}. {self.description}. "
            f"{self.bedrooms} bedrooms, {self.bathrooms} bathrooms, {self.square_feet} sqft. "
            f"Located in {self.city}, {self.state}. Price: ${self.price:,.0f}"
        )


class CallLog(Base):
    """Phone call log entry."""

    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_sid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    direction: Mapped[CallDirection] = mapped_column(Enum(CallDirection), nullable=False)
    from_number: Mapped[str] = mapped_column(String(20), nullable=False)
    to_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[CallStatus] = mapped_column(
        Enum(CallStatus), default=CallStatus.INITIATED, nullable=False
    )
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "call_sid": self.call_sid,
            "direction": self.direction.value,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "status": self.status.value,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


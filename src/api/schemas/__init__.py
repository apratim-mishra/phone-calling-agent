from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CallRequest(BaseModel):
    to_number: str = Field(..., description="Phone number to call (E.164 format)")
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL")


class CallResponse(BaseModel):
    call_sid: str
    status: str
    message: str


class PropertySearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    max_price: Optional[float] = Field(None, description="Maximum price")
    min_bedrooms: Optional[int] = Field(None, description="Minimum bedrooms")
    city: Optional[str] = Field(None, description="City filter")
    limit: int = Field(5, ge=1, le=20, description="Max results")


class PropertyResponse(BaseModel):
    id: str
    score: float
    title: str
    price: float
    bedrooms: int
    bathrooms: float
    city: str
    state: str
    address: Optional[str] = None


class PropertySearchResponse(BaseModel):
    results: list[PropertyResponse]
    total: int
    query: str


class TwilioVoiceWebhook(BaseModel):
    CallSid: str
    AccountSid: str
    From: str
    To: str
    CallStatus: str
    Direction: Optional[str] = None
    ApiVersion: Optional[str] = None


class TwilioStatusWebhook(BaseModel):
    CallSid: str
    CallStatus: str
    CallDuration: Optional[int] = None
    Timestamp: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    code: str
    details: Optional[dict] = None


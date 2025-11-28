import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request

from src.api.schemas import CallRequest, CallResponse, PropertySearchRequest, PropertySearchResponse
from src.database.models import CallDirection
from src.services.call_service import CallService
from src.services.search_service import SearchService
from src.services.twilio_service import TwilioService
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice"])

call_service = CallService()
search_service = SearchService()
twilio_service = TwilioService()


@router.post("/call", response_model=CallResponse)
async def initiate_call(request: CallRequest, req: Request) -> CallResponse:
    """Initiate an outbound call."""
    try:
        base_url = str(req.base_url).rstrip("/")
        webhook_url = request.webhook_url or f"{base_url}/twilio/voice"

        call_sid = await twilio_service.make_call(
            to_number=request.to_number,
            webhook_url=webhook_url,
        )

        return CallResponse(
            call_sid=call_sid,
            status="initiated",
            message=f"Call initiated to {request.to_number}",
        )

    except Exception as e:
        logger.error(f"Failed to initiate call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream/{call_sid}")
async def websocket_stream(websocket: WebSocket, call_sid: str):
    """WebSocket endpoint for real-time audio streaming with Twilio."""
    await websocket.accept()
    logger.info(f"WebSocket connected for call: {call_sid}")

    session = call_service.get_session(call_sid)
    if not session:
        session = await call_service.start_call(
            call_sid=call_sid,
            caller_number="unknown",
            to_number="unknown",
            direction=CallDirection.INBOUND,
        )

    try:
        greeting_audio = await call_service.get_greeting_audio(call_sid)
        if greeting_audio:
            import base64

            await websocket.send_json(
                {
                    "event": "media",
                    "streamSid": call_sid,
                    "media": {"payload": base64.b64encode(greeting_audio).decode()},
                }
            )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            response = await call_service.handle_websocket_message(call_sid, message)

            if response:
                await websocket.send_json(response)

            if message.get("event") == "stop":
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call: {call_sid}")
    except Exception as e:
        logger.error(f"WebSocket error for call {call_sid}: {e}")
    finally:
        await call_service.end_call(call_sid, "WebSocket closed")


@router.post("/properties/search", response_model=PropertySearchResponse)
async def search_properties(request: PropertySearchRequest) -> PropertySearchResponse:
    """Search for properties using semantic search."""
    try:
        results = await search_service.search_properties(
            query=request.query,
            max_price=request.max_price,
            min_bedrooms=request.min_bedrooms,
            city=request.city,
            limit=request.limit,
        )

        property_responses = []
        for r in results:
            property_responses.append(
                {
                    "id": r.get("id", ""),
                    "score": r.get("score", 0.0),
                    "title": r.get("title", ""),
                    "price": r.get("price", 0),
                    "bedrooms": r.get("bedrooms", 0),
                    "bathrooms": r.get("bathrooms", 0),
                    "city": r.get("city", ""),
                    "state": r.get("state", ""),
                    "address": r.get("address"),
                }
            )

        return PropertySearchResponse(
            results=property_responses,
            total=len(property_responses),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Property search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


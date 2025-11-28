from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response

from src.database.models import CallDirection, CallStatus
from src.services.call_service import CallService
from src.services.twilio_service import TwilioService
from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/twilio", tags=["Twilio Webhooks"])

call_service = CallService()
twilio_service = TwilioService()


def _validate_twilio_request(request: Request, form_data: dict) -> bool:
    """Validate incoming Twilio webhook request."""
    if settings.debug:
        return True

    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)

    return twilio_service.validate_request(url, form_data, signature)


@router.post("/voice")
async def handle_voice_webhook(
    request: Request,
    CallSid: str = Form(...),
    AccountSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    Direction: str = Form(None),
):
    """Handle incoming voice webhook from Twilio."""
    form_data = {
        "CallSid": CallSid,
        "AccountSid": AccountSid,
        "From": From,
        "To": To,
        "CallStatus": CallStatus,
        "Direction": Direction or "",
    }

    if not _validate_twilio_request(request, form_data):
        logger.warning(f"Invalid Twilio signature for call {CallSid}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.info(f"Voice webhook: {CallSid} - {CallStatus} from {From}")

    direction = CallDirection.INBOUND if Direction == "inbound" else CallDirection.OUTBOUND

    session = call_service.get_session(CallSid)
    if not session:
        await call_service.start_call(
            call_sid=CallSid,
            caller_number=From,
            to_number=To,
            direction=direction,
        )

    base_url = str(request.base_url).rstrip("/")
    websocket_url = f"wss://{request.url.netloc}/voice/stream/{CallSid}"

    twiml = twilio_service.create_stream_response(websocket_url)

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/status")
async def handle_status_webhook(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: int = Form(None),
):
    """Handle call status updates from Twilio."""
    logger.info(f"Status webhook: {CallSid} - {CallStatus}")

    status_map = {
        "initiated": CallStatus.INITIATED,
        "ringing": CallStatus.RINGING,
        "in-progress": CallStatus.IN_PROGRESS,
        "completed": CallStatus.COMPLETED,
        "failed": CallStatus.FAILED,
        "busy": CallStatus.BUSY,
        "no-answer": CallStatus.NO_ANSWER,
        "canceled": CallStatus.CANCELED,
    }

    db_status = status_map.get(CallStatus.lower())
    if db_status:
        await call_service.update_call_status(CallSid, db_status)

    if CallStatus.lower() in ["completed", "failed", "busy", "no-answer", "canceled"]:
        await call_service.end_call(CallSid, f"Call {CallStatus}")

    return Response(content="", status_code=200)


@router.post("/voice/gather")
async def handle_gather_webhook(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(None),
    Confidence: float = Form(None),
):
    """Handle speech gather results from Twilio."""
    logger.info(f"Gather webhook: {CallSid} - Speech: {SpeechResult}")

    if not SpeechResult:
        twiml = twilio_service.create_gather_response(
            prompt="I didn't catch that. Could you please repeat?",
            action_url=f"/twilio/voice/gather",
        )
        return Response(content=twiml, media_type="application/xml")

    return Response(content="", status_code=200)


@router.post("/voice/fallback")
async def handle_fallback_webhook(
    request: Request,
    CallSid: str = Form(...),
    ErrorCode: str = Form(None),
    ErrorUrl: str = Form(None),
):
    """Handle fallback webhook when primary webhook fails."""
    logger.error(f"Fallback webhook: {CallSid} - Error: {ErrorCode}")

    twiml = twilio_service.create_say_response(
        "I'm sorry, we're experiencing technical difficulties. Please try again later."
    )

    return Response(content=twiml, media_type="application/xml")


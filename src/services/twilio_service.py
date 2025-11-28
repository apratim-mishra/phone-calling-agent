from typing import Optional

from twilio.rest import Client
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

from src.config import settings
from src.utils.errors import TwilioError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TwilioService:
    """Twilio phone service integration."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        phone_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or settings.twilio_account_sid
        self.auth_token = auth_token or settings.twilio_auth_token
        self.phone_number = phone_number or settings.twilio_phone_number
        self._client: Optional[Client] = None
        self._validator: Optional[RequestValidator] = None

    def _get_client(self) -> Client:
        """Get or create Twilio client."""
        if not self.account_sid or not self.auth_token:
            raise TwilioError("Twilio credentials not configured")

        if self._client is None:
            self._client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio client initialized")

        return self._client

    def _get_validator(self) -> RequestValidator:
        """Get or create request validator."""
        if self._validator is None:
            self._validator = RequestValidator(self.auth_token)

        return self._validator

    def validate_request(self, url: str, params: dict, signature: str) -> bool:
        """Validate incoming Twilio webhook request.

        Args:
            url: Full URL of the request
            params: Request parameters
            signature: X-Twilio-Signature header value

        Returns:
            True if request is valid
        """
        try:
            validator = self._get_validator()
            return validator.validate(url, params, signature)
        except Exception as e:
            logger.error(f"Request validation failed: {e}")
            return False

    def create_stream_response(self, websocket_url: str) -> str:
        """Create TwiML response for WebSocket streaming.

        Args:
            websocket_url: WebSocket URL for audio streaming

        Returns:
            TwiML XML string
        """
        response = VoiceResponse()

        connect = Connect()
        stream = Stream(url=websocket_url)
        stream.parameter(name="track", value="both_tracks")
        connect.append(stream)
        response.append(connect)

        return str(response)

    def create_say_response(self, message: str, voice: str = "Polly.Joanna") -> str:
        """Create TwiML response with text-to-speech.

        Args:
            message: Text to speak
            voice: Voice to use

        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        response.say(message, voice=voice)
        return str(response)

    def create_gather_response(
        self,
        prompt: str,
        action_url: str,
        timeout: int = 5,
        voice: str = "Polly.Joanna",
    ) -> str:
        """Create TwiML response for gathering speech input.

        Args:
            prompt: Text to speak before gathering
            action_url: URL to send gathered input
            timeout: Seconds to wait for input
            voice: Voice to use

        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        gather = response.gather(
            input="speech",
            action=action_url,
            timeout=timeout,
            speech_timeout="auto",
        )
        gather.say(prompt, voice=voice)
        return str(response)

    async def make_call(
        self,
        to_number: str,
        webhook_url: str,
        from_number: Optional[str] = None,
    ) -> str:
        """Initiate an outbound call.

        Args:
            to_number: Phone number to call
            webhook_url: URL for call handling webhooks
            from_number: Caller ID (defaults to configured number)

        Returns:
            Call SID
        """
        try:
            client = self._get_client()
            call = client.calls.create(
                to=to_number,
                from_=from_number or self.phone_number,
                url=webhook_url,
                status_callback=f"{webhook_url}/status",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
            )

            logger.info(f"Initiated call to {to_number}: {call.sid}")
            return call.sid

        except Exception as e:
            raise TwilioError(f"Failed to make call: {e}")

    def get_call(self, call_sid: str) -> dict:
        """Get call details.

        Args:
            call_sid: Call SID

        Returns:
            Call details dictionary
        """
        try:
            client = self._get_client()
            call = client.calls(call_sid).fetch()

            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "duration": call.duration,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
            }
        except Exception as e:
            raise TwilioError(f"Failed to get call: {e}")

    def end_call(self, call_sid: str) -> None:
        """End an active call.

        Args:
            call_sid: Call SID to end
        """
        try:
            client = self._get_client()
            client.calls(call_sid).update(status="completed")
            logger.info(f"Ended call: {call_sid}")
        except Exception as e:
            raise TwilioError(f"Failed to end call: {e}")

    def transfer_call(self, call_sid: str, to_number: str) -> None:
        """Transfer a call to another number.

        Args:
            call_sid: Call SID to transfer
            to_number: Number to transfer to
        """
        try:
            client = self._get_client()
            response = VoiceResponse()
            response.dial(to_number)

            client.calls(call_sid).update(twiml=str(response))
            logger.info(f"Transferred call {call_sid} to {to_number}")
        except Exception as e:
            raise TwilioError(f"Failed to transfer call: {e}")


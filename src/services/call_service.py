import asyncio
import base64
import json
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from langchain_core.messages import BaseMessage

from src.agents.voice_agent import VoiceAgent
from src.audio import AudioProcessor, WhisperSTT, KokoroTTS
from src.database import async_session_maker
from src.database.models import CallLog, CallDirection, CallStatus
from src.services.twilio_service import TwilioService
from src.utils.logging import get_logger
from src.utils.monitoring import monitor

logger = get_logger(__name__)


class CallSession:
    """Manages state for an active call."""

    def __init__(self, call_sid: str, caller_number: str, direction: CallDirection):
        self.call_sid = call_sid
        self.caller_number = caller_number
        self.direction = direction
        self.messages: list[BaseMessage] = []
        self.transcription_buffer: list[str] = []
        self.audio_buffer: bytes = b""
        self.start_time = datetime.utcnow()
        self.is_active = True


class CallService:
    """Manages phone call lifecycle and audio processing."""

    def __init__(self):
        self.agent = VoiceAgent()
        self.stt = WhisperSTT()
        self.tts = KokoroTTS()
        self.audio_processor = AudioProcessor()
        self.twilio = TwilioService()
        self._sessions: dict[str, CallSession] = {}

    async def start_call(
        self,
        call_sid: str,
        caller_number: str,
        to_number: str,
        direction: CallDirection,
    ) -> CallSession:
        """Start a new call session.

        Args:
            call_sid: Twilio call SID
            caller_number: Caller's phone number
            to_number: Called phone number
            direction: Call direction (inbound/outbound)

        Returns:
            New CallSession instance
        """
        session = CallSession(call_sid, caller_number, direction)
        self._sessions[call_sid] = session

        async with async_session_maker() as db:
            call_log = CallLog(
                call_sid=call_sid,
                direction=direction,
                from_number=caller_number,
                to_number=to_number,
                status=CallStatus.INITIATED,
            )
            db.add(call_log)
            await db.commit()

        logger.info(f"Started call session: {call_sid}")
        return session

    def get_session(self, call_sid: str) -> Optional[CallSession]:
        """Get an active call session."""
        return self._sessions.get(call_sid)

    async def process_audio_chunk(
        self,
        call_sid: str,
        audio_data: bytes,
        is_final: bool = False,
    ) -> Optional[bytes]:
        """Process incoming audio chunk and return response audio.

        Args:
            call_sid: Call SID
            audio_data: Raw audio bytes (mu-law from Twilio)
            is_final: Whether this is the final chunk (end of speech)

        Returns:
            Response audio bytes (mu-law) or None
        """
        session = self.get_session(call_sid)
        if not session or not session.is_active:
            return None

        session.audio_buffer += audio_data

        if not is_final:
            return None

        try:
            pcm_audio = self.audio_processor.mulaw_to_pcm16(session.audio_buffer)
            float_audio = pcm_audio.astype("float32") / 32768.0

            with monitor.timer("latency/transcription"):
                transcription = await self.stt.transcribe_async(float_audio)

            session.audio_buffer = b""

            if not transcription.strip():
                return None

            session.transcription_buffer.append(f"User: {transcription}")
            logger.debug(f"Transcription [{call_sid}]: {transcription}")

            with monitor.timer("latency/llm"):
                response_text, session.messages, action = await self.agent.process_message(
                    user_input=transcription,
                    call_sid=call_sid,
                    caller_number=session.caller_number,
                    history=session.messages,
                )

            session.transcription_buffer.append(f"Agent: {response_text}")

            with monitor.timer("latency/tts"):
                response_audio = await self.tts.synthesize_async(response_text)

            response_audio_16k = self.audio_processor.resample(
                response_audio,
                orig_sr=self.tts.sample_rate,
                target_sr=8000,
            )

            pcm16 = (response_audio_16k * 32767).astype("int16")
            mulaw_audio = self.audio_processor.pcm16_to_mulaw(pcm16)

            if action == "end":
                await self.end_call(call_sid, "Call completed normally")
            elif action == "transfer":
                logger.info(f"Transfer requested for call {call_sid}")

            return mulaw_audio

        except Exception as e:
            logger.error(f"Error processing audio for {call_sid}: {e}")
            return None

    async def get_greeting_audio(self, call_sid: str) -> bytes:
        """Generate greeting audio for call start.

        Args:
            call_sid: Call SID

        Returns:
            Greeting audio as mu-law bytes
        """
        greeting = await self.agent.get_greeting()

        response_audio = await self.tts.synthesize_async(greeting)
        response_audio_8k = self.audio_processor.resample(
            response_audio,
            orig_sr=self.tts.sample_rate,
            target_sr=8000,
        )

        pcm16 = (response_audio_8k * 32767).astype("int16")
        return self.audio_processor.pcm16_to_mulaw(pcm16)

    async def handle_websocket_message(
        self,
        call_sid: str,
        message: dict,
    ) -> Optional[dict]:
        """Handle incoming WebSocket message from Twilio.

        Args:
            call_sid: Call SID
            message: Parsed WebSocket message

        Returns:
            Response message to send back, or None
        """
        event = message.get("event")

        if event == "start":
            stream_sid = message.get("start", {}).get("streamSid")
            logger.info(f"Stream started: {stream_sid}")
            return None

        elif event == "media":
            payload = message.get("media", {}).get("payload")
            if payload:
                audio_data = base64.b64decode(payload)
                response_audio = await self.process_audio_chunk(
                    call_sid, audio_data, is_final=False
                )
                if response_audio:
                    return {
                        "event": "media",
                        "streamSid": message.get("streamSid"),
                        "media": {"payload": base64.b64encode(response_audio).decode()},
                    }
            return None

        elif event == "mark":
            logger.debug(f"Mark received: {message.get('mark', {}).get('name')}")
            return None

        elif event == "stop":
            logger.info(f"Stream stopped for call {call_sid}")
            await self.end_call(call_sid, "Stream stopped")
            return None

        return None

    async def end_call(self, call_sid: str, reason: str = "") -> None:
        """End a call session.

        Args:
            call_sid: Call SID
            reason: Reason for ending
        """
        session = self._sessions.pop(call_sid, None)
        if not session:
            return

        session.is_active = False
        duration = (datetime.utcnow() - session.start_time).seconds

        async with async_session_maker() as db:
            result = await db.execute(
                select(CallLog).where(CallLog.call_sid == call_sid)
            )
            call_log = result.scalar_one_or_none()

            if call_log:
                call_log.status = CallStatus.COMPLETED
                call_log.duration = duration
                call_log.ended_at = datetime.utcnow()
                call_log.transcription = "\n".join(session.transcription_buffer)
                await db.commit()

        monitor.log_call_metrics(
            call_sid=call_sid,
            duration=duration,
            transcription_latency=0,
            llm_latency=0,
            tts_latency=0,
        )

        logger.info(f"Ended call {call_sid}: {reason} (duration: {duration}s)")

    async def update_call_status(self, call_sid: str, status: CallStatus) -> None:
        """Update call status in database.

        Args:
            call_sid: Call SID
            status: New status
        """
        async with async_session_maker() as db:
            result = await db.execute(
                select(CallLog).where(CallLog.call_sid == call_sid)
            )
            call_log = result.scalar_one_or_none()

            if call_log:
                call_log.status = status
                await db.commit()

        logger.debug(f"Updated call {call_sid} status to {status.value}")


import asyncio
import base64
import json
from typing import Optional
from datetime import datetime, timedelta

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
        self.last_audio_time = datetime.utcnow()
        self.silence_threshold = 1.5  # seconds of silence to trigger processing
        self.min_audio_length = 1600  # minimum bytes (~0.1s at 8kHz mu-law)
        self.is_processing = False
        self.is_speaking = False  # True when TTS audio is being sent
        self.speaking_until: datetime | None = None  # When to stop ignoring input


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
        # Return existing session if already exists
        if call_sid in self._sessions:
            logger.debug(f"Returning existing session for {call_sid}")
            return self._sessions[call_sid]

        session = CallSession(call_sid, caller_number, direction)
        self._sessions[call_sid] = session

        async with async_session_maker() as db:
            # Check if call log already exists
            result = await db.execute(
                select(CallLog).where(CallLog.call_sid == call_sid)
            )
            existing = result.scalar_one_or_none()

            if not existing:
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
            else:
                logger.debug(f"Call log already exists for {call_sid}")

        return session

    def get_session(self, call_sid: str) -> Optional[CallSession]:
        """Get an active call session."""
        return self._sessions.get(call_sid)

    def _detect_silence(self, audio_data: bytes, threshold: int = 10) -> bool:
        """Detect if audio chunk is silence (mu-law).
        
        Args:
            audio_data: Mu-law encoded audio bytes
            threshold: Amplitude threshold for silence detection
            
        Returns:
            True if audio is mostly silence
        """
        if len(audio_data) < 100:
            return False
        # Mu-law silence is around 127-128
        silence_count = sum(1 for b in audio_data if 120 <= b <= 136)
        return silence_count > len(audio_data) * 0.8

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

        if not is_final:
            session.audio_buffer += audio_data
            return None

        # Prevent concurrent processing
        if session.is_processing:
            return None
        session.is_processing = True

        try:
            logger.info(f"🎤 Processing {len(session.audio_buffer)} bytes of audio...")
            pcm_audio = self.audio_processor.mulaw_to_pcm16(session.audio_buffer)
            float_audio = pcm_audio.astype("float32") / 32768.0
            
            # CRITICAL: Resample from 8kHz (Twilio) to 16kHz (Whisper)
            float_audio_16k = self.audio_processor.resample(float_audio, orig_sr=8000, target_sr=16000)
            logger.info(f"🎤 Converted to PCM: {len(pcm_audio)} samples @ 8kHz → {len(float_audio_16k)} samples @ 16kHz, range: [{float_audio_16k.min():.3f}, {float_audio_16k.max():.3f}]")

            with monitor.timer("latency/transcription"):
                transcription = await self.stt.transcribe_async(float_audio_16k)

            session.audio_buffer = b""
            logger.info(f"🎤 Transcription result: '{transcription}'")

            if not transcription.strip():
                logger.warning("🎤 Empty transcription, skipping")
                session.is_processing = False
                return None

            session.transcription_buffer.append(f"User: {transcription}")
            logger.info(f"✅ Transcription [{call_sid}]: {transcription}")

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
                # Schedule hangup after farewell audio plays
                # Audio duration = len(mulaw_audio) / 8000 seconds
                hangup_delay = len(mulaw_audio) / 8000 + 1.0
                logger.info(f"📞 Call ending, will hang up in {hangup_delay:.1f}s after farewell")
                asyncio.create_task(self._delayed_hangup(call_sid, hangup_delay))
            elif action == "transfer":
                logger.info(f"Transfer requested for call {call_sid}")

            session.is_processing = False
            return mulaw_audio

        except Exception as e:
            logger.error(f"Error processing audio for {call_sid}: {e}")
            session.is_processing = False
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
                session = self.get_session(call_sid)
                if session and not session.is_processing:
                    # Echo cancellation: ignore input while we're speaking
                    if session.speaking_until and datetime.utcnow() < session.speaking_until:
                        # Still speaking, discard incoming audio
                        return None
                    elif session.speaking_until:
                        # Just finished speaking, clear buffer and reset
                        session.speaking_until = None
                        session.audio_buffer = b""
                        session.silent_chunks = 0
                        logger.debug("🔇 Finished speaking, now listening")
                    
                    session.audio_buffer += audio_data
                    
                    # Check if we have enough audio
                    buffer_size = len(session.audio_buffer)
                    is_silent = self._detect_silence(audio_data)
                    
                    # Track consecutive silence
                    if is_silent:
                        if not hasattr(session, 'silent_chunks'):
                            session.silent_chunks = 0
                        session.silent_chunks += 1
                    else:
                        session.silent_chunks = 0
                    
                    # Process when: enough audio AND (consecutive silence OR max buffer)
                    should_process = (
                        buffer_size >= 8000 and  # At least 0.5s of audio
                        (getattr(session, 'silent_chunks', 0) >= 15 or buffer_size > 48000)  # ~15 silent chunks or ~3s max
                    )
                    
                    if should_process:
                        logger.info(f"Processing audio: {buffer_size} bytes, silent_chunks: {getattr(session, 'silent_chunks', 0)}")
                        response_audio = await self.process_audio_chunk(
                            call_sid, audio_data, is_final=True
                        )
                        session.silent_chunks = 0  # Reset
                        if response_audio:
                            # Set speaking duration (audio length / 8000 samples per sec)
                            speaking_duration = len(response_audio) / 8000 + 0.5  # Add buffer
                            session.speaking_until = datetime.utcnow() + timedelta(seconds=speaking_duration)
                            logger.info(f"📤 Sending {len(response_audio)} bytes ({speaking_duration:.1f}s) of response audio")
                            return {
                                "event": "media",
                                "streamSid": message.get("streamSid"),
                                "media": {"payload": base64.b64encode(response_audio).decode()},
                            }
                        else:
                            logger.warning("⚠️ No response audio generated")
            return None

        elif event == "mark":
            logger.debug(f"Mark received: {message.get('mark', {}).get('name')}")
            return None

        elif event == "stop":
            logger.info(f"Stream stopped for call {call_sid}")
            await self.end_call(call_sid, "Stream stopped")
            return None

        return None

    async def _delayed_hangup(self, call_sid: str, delay: float) -> None:
        """Hang up call after a delay (to allow farewell audio to play).

        Args:
            call_sid: Call SID
            delay: Seconds to wait before hanging up
        """
        await asyncio.sleep(delay)
        await self.end_call(call_sid, "Goodbye - call ended by user", hangup=True)

    async def end_call(self, call_sid: str, reason: str = "", hangup: bool = False) -> None:
        """End a call session.

        Args:
            call_sid: Call SID
            reason: Reason for ending
            hangup: Whether to actually hang up the call via Twilio API
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

        # Hang up via Twilio API if requested
        if hangup:
            try:
                self.twilio.end_call(call_sid)
                logger.info(f"📞 Hung up call {call_sid}")
            except Exception as e:
                logger.warning(f"Failed to hang up call {call_sid}: {e}")

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


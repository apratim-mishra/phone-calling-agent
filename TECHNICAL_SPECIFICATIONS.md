# Technical Specifications

## System Requirements

### Hardware

- **Development**: Apple Silicon Mac (M1/M2/M3) with 16GB+ RAM
- **Production**: 4 vCPU, 8GB RAM minimum

### Software

- Python 3.10+
- macOS 13+ or Ubuntu 22.04+

## Audio Specifications

| Parameter   | Input              | Output       |
| ----------- | ------------------ | ------------ |
| Format      | μ-law, PCM16, Opus | PCM16, μ-law |
| Sample Rate | 16kHz              | 16kHz/24kHz  |
| Channels    | Mono               | Mono         |

## Model Configurations

### Whisper (STT)

| Model   | VRAM | Latency | Accuracy |
| ------- | ---- | ------- | -------- |
| tiny    | ~1GB | ~200ms  | 75%      |
| base ⭐ | ~2GB | ~350ms  | 85%      |
| small   | ~5GB | ~800ms  | 90%      |

### Kokoro (TTS)

- Model: kokoro-v0_19
- Voice: af_sarah
- Alternatives: Piper TTS, Coqui TTS, StyleTTS2

### LLM

- Primary: Z.ai
- Fallback: OpenAI gpt-4o-mini
- Max tokens: 150, Temperature: 0.7

## API Endpoints

| Method | Endpoint             | Description     |
| ------ | -------------------- | --------------- |
| GET    | `/health`            | Health check    |
| WS     | `/voice/stream`      | Audio streaming |
| POST   | `/voice/call`        | Initiate call   |
| POST   | `/twilio/voice`      | Twilio webhook  |
| POST   | `/properties/search` | Semantic search |

## Database Schema

### Properties

- id, title, description, price, bedrooms, bathrooms
- square_feet, location, address, city, state, zip_code
- embedding_id, created_at, updated_at

### Call Logs

- id, call_sid, direction, from_number, to_number
- status, duration, transcription, summary
- created_at, ended_at

## Error Codes

| Code | Description                      |
| ---- | -------------------------------- |
| E001 | Transcription failed             |
| E002 | TTS generation failed            |
| E003 | LLM request failed               |
| E004 | Vector search failed             |
| E005 | Twilio webhook validation failed |

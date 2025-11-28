# Realtime Phone Agent System

AI phone agent powered by open-source models on Apple Silicon via MLX.

## Features

- 📞 Inbound & outbound calls via Twilio
- 🎤 Speech-to-text with Whisper (MLX)
- 🗣️ Text-to-speech with Kokoro
- 🧠 Agent reasoning with LangGraph
- 🔍 Semantic search via Pinecone

## Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Architecture and features |
| [TECHNICAL_SPECIFICATIONS.md](TECHNICAL_SPECIFICATIONS.md) | Technical specs and API reference |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Code organization |

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example.txt .env

# Initialize
python scripts/setup_pinecone.py
python scripts/seed_data.py

# Run
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Tunnel (dev)
ngrok http 8000
```

Configure Twilio webhook to: `https://your-domain.ngrok.io/twilio/voice`

## Architecture

```
Phone → Twilio → FastAPI → Whisper → LangGraph → Kokoro → Response
                                         ↓
                                     Pinecone
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Agent | LangGraph |
| ML | MLX |
| STT | Whisper |
| TTS | Kokoro |
| LLM | Z.ai / OpenAI |
| Vector DB | Pinecone |
| Phone | Twilio |

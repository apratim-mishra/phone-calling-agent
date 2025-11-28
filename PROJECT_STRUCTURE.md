# Project Structure

```
phone_calling/
├── .cursorrules
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_OVERVIEW.md
├── TECHNICAL_SPECIFICATIONS.md
├── requirements.txt
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Pydantic Settings
│   │
│   ├── agents/                  # LangGraph agents
│   │   ├── __init__.py
│   │   ├── voice_agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   │
│   ├── audio/                   # Audio processing
│   │   ├── __init__.py
│   │   ├── stt.py               # Whisper
│   │   ├── tts.py               # Kokoro
│   │   └── processor.py
│   │
│   ├── models/                  # ML wrappers
│   │   ├── __init__.py
│   │   ├── provider.py          # LLM abstraction
│   │   └── embeddings.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── pinecone_client.py
│   │   └── models.py            # SQLAlchemy
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── voice.py
│   │   │   └── webhooks.py
│   │   └── schemas/
│   │
│   ├── services/
│   │   ├── call_service.py
│   │   ├── search_service.py
│   │   └── twilio_service.py
│   │
│   └── utils/
│       ├── logging.py
│       ├── monitoring.py
│       └── errors.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── scripts/
│   ├── setup_pinecone.py
│   └── seed_data.py
│
└── data/
    └── app.db
```

## Key Files

| File | Purpose |
|------|---------|
| `src/api/main.py` | FastAPI entry point |
| `src/config.py` | Environment configuration |
| `src/agents/voice_agent.py` | LangGraph agent |
| `src/audio/stt.py` | Whisper transcription |
| `src/audio/tts.py` | Kokoro synthesis |
| `src/api/routes/webhooks.py` | Twilio handlers |
| `src/database/pinecone_client.py` | Vector search |

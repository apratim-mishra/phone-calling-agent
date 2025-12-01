# 📞 Realtime Phone Agent

AI-powered phone agent for real estate that handles inbound calls, understands natural language, and searches properties - all running on Apple Silicon with local ML models.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![MLX](https://img.shields.io/badge/MLX-Apple%20Silicon-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 📞 **Phone Integration** - Inbound/outbound calls via Twilio
- 🎤 **Speech-to-Text** - Local Whisper (MLX) or Groq API
- 🔊 **Text-to-Speech** - Kokoro TTS with natural voices
- 🧠 **Smart Agent** - LangGraph-powered conversation flow
- 🔍 **Property Search** - Semantic search via Pinecone
- 📊 **Call Logging** - SQLite database for call history
- 🚀 **Fast Inference** - Groq LLM for sub-second responses

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Phone     │────▶│   Twilio    │────▶│   FastAPI   │
│   Call      │◀────│   WebSocket │◀────│   Server    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
              ┌─────▼─────┐            ┌───────▼───────┐          ┌───────▼───────┐
              │  Whisper  │            │   LangGraph   │          │    Kokoro     │
              │   (STT)   │            │    Agent      │          │    (TTS)      │
              │   MLX     │            │               │          │    MLX        │
              └───────────┘            └───────┬───────┘          └───────────────┘
                                               │
                                       ┌───────▼───────┐
                                       │   Pinecone    │
                                       │ Property DB   │
                                       └───────────────┘
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and enter directory
cd phone_calling

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment

```bash
# Copy example env file
cp env.example.txt .env

# Edit .env with your API keys:
# - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
# - GROQ_API_KEY (recommended for fast LLM)
# - PINECONE_API_KEY
# - OPENAI_API_KEY (for embeddings)
```

### 3. Initialize Database

```bash
# Setup Pinecone index
python scripts/setup_pinecone.py

# Seed sample properties
python scripts/seed_data.py
```

### 4. Run Server

```bash
# Start the server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# In another terminal, start ngrok for Twilio webhooks
ngrok http 8000
```

### 5. Configure Twilio

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to Phone Numbers → Your Number
3. Set Voice webhook URL to: `https://your-ngrok-url.ngrok.io/twilio/voice`
4. Call your Twilio number to test!

## 📁 Project Structure

```
phone_calling/
├── src/
│   ├── agents/          # LangGraph agent & tools
│   ├── api/             # FastAPI routes
│   ├── audio/           # STT (Whisper) & TTS (Kokoro)
│   ├── database/        # SQLite & Pinecone
│   ├── models/          # LLM providers
│   ├── services/        # Business logic
│   └── utils/           # Logging, errors, monitoring
├── scripts/             # Setup & seed scripts
├── tests/               # Unit & integration tests
└── data/                # SQLite database
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API** | FastAPI | WebSocket & REST endpoints |
| **Agent** | LangGraph | Conversation state machine |
| **STT** | MLX Whisper | Speech-to-text (local) |
| **TTS** | Kokoro | Text-to-speech (local) |
| **LLM** | Groq / Z.ai / OpenAI | Response generation |
| **Vector DB** | Pinecone | Property semantic search |
| **Database** | SQLite | Call logs & properties |
| **Phone** | Twilio | Voice calls & streaming |

## 🔧 Configuration

### LLM Providers (in order of preference)

1. **Groq** - Fastest (~0.5-2s responses) - Recommended for phone
2. **Z.ai** - Good quality but slower (~3-14s)
3. **OpenAI** - Fallback option

### Environment Variables

```env
# Required
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
PINECONE_API_KEY=xxxxx
OPENAI_API_KEY=sk-xxxxx  # For embeddings

# Recommended for speed
GROQ_API_KEY=gsk_xxxxx
GROQ_MODEL=llama-3.1-70b-versatile

# Optional
DEBUG=true  # Skip Twilio signature validation (dev only)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## 📞 Example Conversation

```
📞 Incoming call...

🤖: "Hi! This is Sarah from Premier Properties. How can I help you?"

👤: "I'm looking for a house in Dallas, Texas"

🤖: "Great! What's your budget range?"

👤: "Around 500 thousand dollars"

🤖: "How many bedrooms do you need?"

👤: "3 bedrooms"

🤖: "I found some options! There's an Oak Cliff Bungalow 
     for $425,000 with 3 beds, and an Uptown High-Rise 
     for $520,000 with 2 beds. Would you like more details?"

👤: "Thanks, bye!"

🤖: "Thanks for calling! Goodbye!"

📞 Call ended
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | High-level architecture |
| [TECHNICAL_SPECIFICATIONS.md](TECHNICAL_SPECIFICATIONS.md) | API reference & specs |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Code organization |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ using MLX, LangGraph, and FastAPI

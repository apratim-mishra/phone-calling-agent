# Realtime Phone Agent System

## Project Description

A production-ready AI phone agent system that can receive and make phone calls, powered by open-source models running on Apple Silicon via MLX. The system handles real-time voice conversations, searches through property data using semantic search, and integrates with phone networks through Twilio.

## Core Capabilities

- **Inbound Calls**: Receive phone calls and respond in real-time
- **Outbound Calls**: Initiate calls to phone numbers
- **Voice Interaction**: Natural speech-to-text and text-to-speech processing
- **Semantic Search**: Query structured data using natural language
- **Real-time Streaming**: Sub-second latency audio processing

## Technology Stack

| Category       | Technologies                                        |
| -------------- | --------------------------------------------------- |
| Core Framework | FastAPI, LangGraph, FastRTC                         |
| ML & Models    | MLX, Whisper (STT), Kokoro (TTS), Z.ai/OpenAI (LLM) |
| Data & Storage | Pinecone, SQLite/PostgreSQL                         |
| Infrastructure | Twilio, Ngrok, Weights & Biases                     |

## Architecture

```
┌─────────────┐
│   Phone     │
│   Network   │
└──────┬──────┘
       │
┌──────▼──────┐
│   Twilio    │
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│       FastAPI Application        │
│                                  │
│  Audio → Whisper → LangGraph    │
│            ↓           ↓        │
│         Agent ← Pinecone        │
│            ↓                    │
│         Kokoro → Response       │
└─────────────────────────────────┘
```

## Performance Targets

| Metric                 | Target |
| ---------------------- | ------ |
| Transcription Latency  | <500ms |
| LLM Response Time      | <2s    |
| TTS Generation         | <800ms |
| Total Response Latency | <3s    |
| Concurrent Calls       | 10+    |

# Audio Recorder & Playback System with AI Agents + MCP

End-to-end audio platform with:

- FastAPI backend (JWT auth, upload, metadata, streaming)
- PostgreSQL + async SQLAlchemy
- React frontend (recording, playback, search, AI assistant UI)
- MCP server exposing recording intelligence tools
- AI agent orchestration for multi-step reasoning over recordings
- CLI acceptance tests + AI CLI commands

## Table of Contents

1. System Overview
2. Architecture
3. Project Structure
4. Core Features
5. AI Features
6. MCP Server
7. Agent Orchestration
8. API Reference
9. Database & Migrations
10. Setup Guide
11. CLI Usage
12. Security & Safety
13. Troubleshooting
14. Next Improvements

## 1) System Overview

The system allows authenticated users to:

- Record/upload audio
- Store audio files and metadata
- List, play, and delete recordings
- Transcribe recordings
- Search recordings semantically (vector search)
- Summarize recordings
- Ask questions across recording transcripts

## 2) Architecture

### Backend

- Framework: FastAPI
- Auth: JWT bearer tokens
- ORM: SQLAlchemy async
- DB: PostgreSQL + pgvector
- AI service layer:
  - transcription
  - embeddings
  - summarization
  - question answering

### Frontend

- React + TypeScript
- Audio capture via `MediaRecorder`
- Dashboard playback/list/search
- AI assistant chat panel with reasoning steps

### AI/MCP

- MCP server (Python MCP SDK) provides structured tools
- Agent orchestrates tool calls based on user query intent
- Backend `/agent/query` also provides API-based orchestration with step traces

## 3) Project Structure

```text
agent/                         # MCP-connected agent orchestration
backend/
  app/
    api/routes/                # auth, recordings, agent routes
    core/                      # config, database, security
    models/                    # SQLAlchemy models
    schemas/                   # Pydantic schemas
    services/                  # auth, recording, AI, agent services
  migrations/                  # SQL migration for AI extensions
  API_CONTRACT_AI.md           # AI endpoint contracts
cli/
  test_api.py                  # acceptance tests
  ai_cli.py                    # AI-focused CLI commands
frontend/
  src/
    pages/Dashboard.tsx        # recorder + recordings + assistant UI
    services/api.ts            # frontend API client
mcp_server/
  server.py                    # MCP tool server
```

## 4) Core Features

Already supported:

- User registration/login
- Audio upload
- File storage under `uploads/audio/<user_id>/...`
- Metadata persistence
- Recordings list
- Recording stream endpoint
- Delete recording

## 5) AI Features

### Data model extension

`AudioRecording` includes:

- `transcript` (`TEXT`)
- `transcript_embedding` (`VECTOR(1536)`)

### AI endpoints

- `POST /recordings/{id}/transcribe`
- `POST /recordings/search`
- `POST /recordings/{id}/summarize`
- `POST /recordings/answer`
- `POST /agent/query`

Detailed payloads are documented in:
- [backend/API_CONTRACT_AI.md](C:/Users/jonad/Audio-Generation/backend/API_CONTRACT_AI.md)

### Provider routing model

The backend supports split providers per capability:

- transcription provider
- embedding provider
- chat provider

Each can use separate `API_KEY`, `BASE_URL`, and `MODEL`, with fallback to `OPENAI_*`.

## 6) MCP Server

MCP tool server:
- [mcp_server/server.py](C:/Users/jonad/Audio-Generation/mcp_server/server.py)

Tools:

- `list_recordings(user_id, token?)`
- `get_recording_metadata(recording_id, token?)`
- `transcribe_audio(recording_id, token?)`
- `summarize_audio(recording_id, token?)`
- `search_recordings(query, limit?, token?)`
- `answer_question_about_recordings(question, limit?, token?)`

All tool inputs/outputs are structured and JWT-scoped through backend APIs.

## 7) Agent Orchestration

### MCP-connected agent module

- [agent/mcp_agent.py](C:/Users/jonad/Audio-Generation/agent/mcp_agent.py)

Supported patterns:

- "Show my latest recording"
- "Summarize my latest recording"
- "Find recordings mentioning deadlines"
- "What did I say about the meeting?"

### Backend API agent endpoint

- `POST /agent/query`
- Returns:
  - final `answer`
  - list of `steps` with tools + previews

## 8) API Reference (quick)

### Auth

- `POST /auth/register`
- `POST /auth/login`

### Recordings

- `POST /recordings/upload`
- `GET /recordings`
- `GET /recordings/{id}`
- `DELETE /recordings/{id}`
- `GET /recordings/{id}/stream`

### AI

- `POST /recordings/{id}/transcribe`
- `POST /recordings/search`
- `POST /recordings/{id}/summarize`
- `POST /recordings/answer`
- `POST /agent/query`

## 9) Database & Migrations

Migration file:

- [backend/migrations/001_ai_extensions.sql](C:/Users/jonad/Audio-Generation/backend/migrations/001_ai_extensions.sql)

What it does:

- enables `vector` extension
- adds transcript fields
- adds ivfflat vector index

## 10) Setup Guide

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL with `pgvector`

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env` from `.env.example`.

Run migration:

```sql
-- execute backend/migrations/001_ai_extensions.sql
```

Start API:

```powershell
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm start
```

### MCP Server

```powershell
cd mcp_server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

## 11) CLI Usage

### Acceptance test suite

```powershell
cd cli
python test_api.py run-tests
```

### AI commands

```powershell
cd cli
python ai_cli.py transcribe-recording 42 --email you@example.com
python ai_cli.py summarize-recording 42 --email you@example.com
python ai_cli.py search-recordings "deadlines" --email you@example.com
python ai_cli.py ask-agent "What did I say about project deadlines?" --user-id 1 --email you@example.com
```

## 12) Security & Safety

Implemented controls:

- JWT enforcement for all user recording access
- user-scoped DB queries (`recording.user_id == current_user.id`)
- prompt-injection pattern blocking for AI query fields
- input sanitization + max length limits
- structured tool inputs/outputs in MCP

Additional recommended hardening:

- rate limiting per user for AI endpoints
- audit log for AI tool invocations
- strict MIME/codec checks on upload
- background jobs + retries for transcription

## 13) Troubleshooting

### `pgvector` not found

- Ensure PostgreSQL extension is installed and run:
  - `CREATE EXTENSION IF NOT EXISTS vector;`

### Transcription fails with OpenRouter

- Some providers may not support `/audio/transcriptions` the same way.
- Use split provider config:
  - chat via OpenRouter
  - transcription/embedding via OpenAI-compatible endpoint with those APIs.

### `EMBEDDING_API_KEY (or OPENAI_API_KEY fallback) is not configured`

- Set at least one key in `backend/.env`:
  - `OPENAI_API_KEY=<your_key>` (shared fallback for all AI capabilities), or
  - `EMBEDDING_API_KEY=<your_key>` (embedding-only override)
- Restart the backend after editing `.env`.

### Windows PowerShell `npm.ps1` blocked

- Run npm via `cmd /c npm ...` or adjust execution policy.

## 14) Next Improvements

1. Replace raw SQL migrations with Alembic migration pipeline.
2. Add async background worker for transcription/embedding jobs.
3. Add integration tests for AI endpoints and agent flows.
4. Add token usage/cost tracking for AI operations.

# AI API Contract

## Authentication

All endpoints below require:

- `Authorization: Bearer <jwt>`

## 1) Transcribe Recording

### `POST /recordings/{id}/transcribe`

Transcribes one recording and stores transcript + embedding.

#### Response `200`

```json
{
  "recording_id": 42,
  "transcript": "Full transcript text...",
  "transcript_preview": "First 240 chars..."
}
```

#### Errors

- `404` recording not found (or not owned by caller)
- `503` transcription provider unavailable / misconfigured

## 2) Semantic Search

### `POST /recordings/search`

#### Request

```json
{
  "query": "deadline discussion",
  "limit": 5
}
```

#### Response `200`

```json
{
  "query": "deadline discussion",
  "total_matches": 2,
  "results": [
    {
      "id": 42,
      "filename": "meeting.webm",
      "duration": 135,
      "created_at": "2026-03-04T12:00:00",
      "transcript_preview": "We discussed project deadlines..."
    }
  ]
}
```

#### Errors

- `400` invalid query / blocked by guardrail / embedding failure

## 3) Summarize Recording

### `POST /recordings/{id}/summarize`

Transcribes first if transcript is missing.

#### Response `200`

```json
{
  "recording_id": 42,
  "summary": "Concise summary of the recording."
}
```

## 4) Ask Question Across Recordings

### `POST /recordings/answer`

#### Request

```json
{
  "question": "What did I say about deadlines?",
  "limit": 5
}
```

#### Response `200`

```json
{
  "question": "What did I say about deadlines?",
  "answer": "You said deadlines were moved to next Friday.",
  "matched_recording_ids": [42, 43]
}
```

## 5) Agent Query (Reasoning + Tools)

### `POST /agent/query`

#### Request

```json
{
  "query": "Summarize my latest recording."
}
```

#### Response `200`

```json
{
  "query": "Summarize my latest recording.",
  "answer": "Summary text...",
  "steps": [
    {
      "step": "1",
      "tool": "list_recordings",
      "input": {"user_id": 1},
      "output_preview": "Found 4 recordings"
    }
  ]
}
```


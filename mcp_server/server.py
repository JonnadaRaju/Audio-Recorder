from __future__ import annotations

import os
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP


API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_TOKEN = os.getenv("MCP_API_TOKEN")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("MCP_REQUEST_TIMEOUT_SECONDS", "20"))

mcp = FastMCP("audio-intelligence-mcp")

INJECTION_MARKERS = (
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "tool instructions",
    "bypass security",
)


def _sanitize_text(value: str) -> str:
    return value.strip()[:4000]


def _ensure_safe_text(value: str) -> str:
    sanitized = _sanitize_text(value)
    lowered = sanitized.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        raise ValueError("Blocked potential prompt injection payload.")
    return sanitized


def _headers(token: str | None = None) -> dict[str, str]:
    effective = token or API_TOKEN
    if not effective:
        raise ValueError("Missing auth token. Set MCP_API_TOKEN or pass token input.")
    return {"Authorization": f"Bearer {effective}"}


def _request(
    method: str,
    endpoint: str,
    *,
    token: str | None = None,
    json_payload: dict[str, Any] | None = None,
) -> Any:
    response = requests.request(
        method=method,
        url=f"{API_BASE_URL}{endpoint}",
        headers=_headers(token),
        json=json_payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if not response.ok:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise RuntimeError(f"{method} {endpoint} failed: {response.status_code} {detail}")
    if response.status_code == 204:
        return {}
    return response.json()


@mcp.tool()
def list_recordings(user_id: int, token: str | None = None) -> dict[str, Any]:
    """
    Return authenticated user's recordings.
    Input is structured by user_id; authorization is enforced via JWT token.
    """
    recordings = _request("GET", "/recordings", token=token)
    return {
        "user_id": user_id,
        "count": len(recordings),
        "recordings": recordings,
    }


@mcp.tool()
def get_recording_metadata(recording_id: int, token: str | None = None) -> dict[str, Any]:
    """Get metadata for one recording owned by authenticated user."""
    recording = _request("GET", f"/recordings/{recording_id}", token=token)
    return {
        "recording_id": recording["id"],
        "filename": recording["filename"],
        "duration": recording.get("duration"),
        "size": recording.get("file_size"),
        "created_at": recording.get("created_at"),
    }


@mcp.tool()
def transcribe_audio(recording_id: int, token: str | None = None) -> dict[str, Any]:
    """Transcribe a recording and return transcript."""
    payload = _request("POST", f"/recordings/{recording_id}/transcribe", token=token)
    return {
        "recording_id": payload["recording_id"],
        "transcript": payload["transcript"],
        "transcript_preview": payload["transcript_preview"],
    }


@mcp.tool()
def summarize_audio(recording_id: int, token: str | None = None) -> dict[str, Any]:
    """Summarize a recording transcript."""
    payload = _request("POST", f"/recordings/{recording_id}/summarize", token=token)
    return {
        "recording_id": payload["recording_id"],
        "summary": payload["summary"],
    }


@mcp.tool()
def search_recordings(query: str, limit: int = 5, token: str | None = None) -> dict[str, Any]:
    """Semantic search over transcripts with prompt-injection checks."""
    safe_query = _ensure_safe_text(query)
    payload = _request(
        "POST",
        "/recordings/search",
        token=token,
        json_payload={"query": safe_query, "limit": max(1, min(limit, 25))},
    )
    return payload


@mcp.tool()
def answer_question_about_recordings(
    question: str, limit: int = 5, token: str | None = None
) -> dict[str, Any]:
    """Answer question using transcript search and grounded generation."""
    safe_question = _ensure_safe_text(question)
    payload = _request(
        "POST",
        "/recordings/answer",
        token=token,
        json_payload={"question": safe_question, "limit": max(1, min(limit, 10))},
    )
    return payload


if __name__ == "__main__":
    mcp.run()


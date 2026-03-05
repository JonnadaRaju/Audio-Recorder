from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class AgentResult:
    answer: str
    steps: list[dict[str, Any]]


class RecordingMCPAgent:
    def __init__(self, user_id: int, token: str | None = None):
        self.user_id = user_id
        self.token = token

    async def run(self, query: str) -> AgentResult:
        steps: list[dict[str, Any]] = []
        normalized = query.lower().strip()

        if not normalized:
            return AgentResult(answer="Query cannot be empty.", steps=steps)

        async with self._session() as session:
            wants_video = "video" in normalized
            wants_audio = "audio" in normalized or "recording" in normalized
            wants_summary = "summarize" in normalized or "summary" in normalized
            wants_latest = any(token in normalized for token in ("latest", "last", "recent"))
            wants_search = any(token in normalized for token in ("find", "search", "mention", "show"))

            if wants_latest and wants_summary and wants_video:
                return await self._summarize_latest_video(session, query, steps)

            if wants_latest and wants_summary and wants_audio and not wants_video:
                return await self._summarize_latest_audio(session, query, steps)

            if wants_latest and wants_summary and not wants_video and not wants_audio:
                return await self._summarize_latest_media(session, query, steps)

            if "recent" in normalized or "show" in normalized or "list" in normalized:
                return await self._list_recent_media(session, query, steps, wants_audio, wants_video)

            if wants_search:
                return await self._search_media(session, query, steps, wants_audio, wants_video)

            if wants_video and not wants_audio:
                qa_result = await self._call_tool(
                    session,
                    "answer_question_about_videos",
                    {"question": query, "limit": 5, "token": self.token},
                )
                steps.append(
                    {
                        "tool": "answer_question_about_videos",
                        "input": {"question": query, "limit": 5},
                        "output_preview": qa_result.get("answer", "")[:120],
                    }
                )
                return AgentResult(answer=qa_result.get("answer", ""), steps=steps)

            if wants_audio and not wants_video:
                qa_result = await self._call_tool(
                    session,
                    "answer_question_about_recordings",
                    {"question": query, "limit": 5, "token": self.token},
                )
                steps.append(
                    {
                        "tool": "answer_question_about_recordings",
                        "input": {"question": query, "limit": 5},
                        "output_preview": qa_result.get("answer", "")[:120],
                    }
                )
                return AgentResult(answer=qa_result.get("answer", ""), steps=steps)

            audio_answer = await self._call_tool(
                session,
                "answer_question_about_recordings",
                {"question": query, "limit": 3, "token": self.token},
            )
            video_answer = await self._call_tool(
                session,
                "answer_question_about_videos",
                {"question": query, "limit": 3, "token": self.token},
            )
            steps.append(
                {
                    "tool": "answer_question_about_recordings",
                    "input": {"question": query, "limit": 3},
                    "output_preview": audio_answer.get("answer", "")[:120],
                }
            )
            steps.append(
                {
                    "tool": "answer_question_about_videos",
                    "input": {"question": query, "limit": 3},
                    "output_preview": video_answer.get("answer", "")[:120],
                }
            )

            combined = (
                "Audio context answer:\n"
                f"{audio_answer.get('answer', 'No audio context found.')}\n\n"
                "Video context answer:\n"
                f"{video_answer.get('answer', 'No video context found.')}"
            )
            return AgentResult(answer=combined, steps=steps)

    async def _summarize_latest_audio(
        self,
        session: ClientSession,
        query: str,
        steps: list[dict[str, Any]],
    ) -> AgentResult:
        list_result = await self._call_tool(
            session,
            "list_recordings",
            {"user_id": self.user_id, "token": self.token},
        )
        recordings = list_result.get("recordings", [])
        steps.append(
            {
                "tool": "list_recordings",
                "input": {"user_id": self.user_id},
                "output_preview": f"Found {len(recordings)} recordings",
            }
        )
        if not recordings:
            return AgentResult(answer="No recordings found.", steps=steps)

        recording_id = recordings[0]["id"]
        await self._call_tool(
            session,
            "transcribe_audio",
            {"recording_id": recording_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "transcribe_audio",
                "input": {"recording_id": recording_id},
                "output_preview": f"Transcribed recording {recording_id}",
            }
        )

        summary_result = await self._call_tool(
            session,
            "summarize_audio",
            {"recording_id": recording_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "summarize_audio",
                "input": {"recording_id": recording_id},
                "output_preview": summary_result.get("summary", "")[:120],
            }
        )
        return AgentResult(answer=summary_result.get("summary", ""), steps=steps)

    async def _summarize_latest_video(
        self,
        session: ClientSession,
        query: str,
        steps: list[dict[str, Any]],
    ) -> AgentResult:
        list_result = await self._call_tool(
            session,
            "list_videos",
            {"user_id": self.user_id, "token": self.token},
        )
        videos = list_result.get("videos", [])
        steps.append(
            {
                "tool": "list_videos",
                "input": {"user_id": self.user_id},
                "output_preview": f"Found {len(videos)} videos",
            }
        )
        if not videos:
            return AgentResult(answer="No videos found.", steps=steps)

        video_id = videos[0]["id"]
        await self._call_tool(
            session,
            "transcribe_video",
            {"video_id": video_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "transcribe_video",
                "input": {"video_id": video_id},
                "output_preview": f"Transcribed video {video_id}",
            }
        )

        summary_result = await self._call_tool(
            session,
            "summarize_video",
            {"video_id": video_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "summarize_video",
                "input": {"video_id": video_id},
                "output_preview": summary_result.get("summary", "")[:120],
            }
        )
        return AgentResult(answer=summary_result.get("summary", ""), steps=steps)

    async def _summarize_latest_media(
        self,
        session: ClientSession,
        query: str,
        steps: list[dict[str, Any]],
    ) -> AgentResult:
        list_audio = await self._call_tool(
            session,
            "list_recordings",
            {"user_id": self.user_id, "token": self.token},
        )
        list_video = await self._call_tool(
            session,
            "list_videos",
            {"user_id": self.user_id, "token": self.token},
        )
        recordings = list_audio.get("recordings", [])
        videos = list_video.get("videos", [])

        steps.append(
            {
                "tool": "list_recordings",
                "input": {"user_id": self.user_id},
                "output_preview": f"Found {len(recordings)} recordings",
            }
        )
        steps.append(
            {
                "tool": "list_videos",
                "input": {"user_id": self.user_id},
                "output_preview": f"Found {len(videos)} videos",
            }
        )

        candidates: list[tuple[str, str, int]] = []
        if recordings:
            candidates.append((
                "audio",
                recordings[0].get("created_at", ""),
                recordings[0].get("id"),
            ))
        if videos:
            candidates.append((
                "video",
                videos[0].get("created_at", ""),
                videos[0].get("id"),
            ))

        if not candidates:
            return AgentResult(answer="No recordings or videos found.", steps=steps)

        candidates.sort(key=lambda item: item[1], reverse=True)
        media_type, _, media_id = candidates[0]
        if media_type == "video":
            return await self._summarize_specific_video(session, media_id, steps)
        return await self._summarize_specific_audio(session, media_id, steps)

    async def _summarize_specific_audio(
        self,
        session: ClientSession,
        recording_id: int,
        steps: list[dict[str, Any]],
    ) -> AgentResult:
        await self._call_tool(
            session,
            "transcribe_audio",
            {"recording_id": recording_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "transcribe_audio",
                "input": {"recording_id": recording_id},
                "output_preview": f"Transcribed recording {recording_id}",
            }
        )
        summary_result = await self._call_tool(
            session,
            "summarize_audio",
            {"recording_id": recording_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "summarize_audio",
                "input": {"recording_id": recording_id},
                "output_preview": summary_result.get("summary", "")[:120],
            }
        )
        return AgentResult(answer=summary_result.get("summary", ""), steps=steps)

    async def _summarize_specific_video(
        self,
        session: ClientSession,
        video_id: int,
        steps: list[dict[str, Any]],
    ) -> AgentResult:
        await self._call_tool(
            session,
            "transcribe_video",
            {"video_id": video_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "transcribe_video",
                "input": {"video_id": video_id},
                "output_preview": f"Transcribed video {video_id}",
            }
        )
        summary_result = await self._call_tool(
            session,
            "summarize_video",
            {"video_id": video_id, "token": self.token},
        )
        steps.append(
            {
                "tool": "summarize_video",
                "input": {"video_id": video_id},
                "output_preview": summary_result.get("summary", "")[:120],
            }
        )
        return AgentResult(answer=summary_result.get("summary", ""), steps=steps)

    async def _list_recent_media(
        self,
        session: ClientSession,
        query: str,
        steps: list[dict[str, Any]],
        wants_audio: bool,
        wants_video: bool,
    ) -> AgentResult:
        if wants_video and not wants_audio:
            list_result = await self._call_tool(
                session,
                "list_videos",
                {"user_id": self.user_id, "token": self.token},
            )
            videos = list_result.get("videos", [])
            steps.append(
                {
                    "tool": "list_videos",
                    "input": {"user_id": self.user_id},
                    "output_preview": f"Found {len(videos)} videos",
                }
            )
            if not videos:
                return AgentResult(answer="No videos found.", steps=steps)
            lines = [f"- [video] #{v['id']} {v['filename']}" for v in videos[:8]]
            return AgentResult(answer="Recent videos:\n" + "\n".join(lines), steps=steps)

        if wants_audio and not wants_video:
            list_result = await self._call_tool(
                session,
                "list_recordings",
                {"user_id": self.user_id, "token": self.token},
            )
            recordings = list_result.get("recordings", [])
            steps.append(
                {
                    "tool": "list_recordings",
                    "input": {"user_id": self.user_id},
                    "output_preview": f"Found {len(recordings)} recordings",
                }
            )
            if not recordings:
                return AgentResult(answer="No recordings found.", steps=steps)
            lines = [f"- [audio] #{r['id']} {r['filename']}" for r in recordings[:8]]
            return AgentResult(answer="Recent recordings:\n" + "\n".join(lines), steps=steps)

        list_audio = await self._call_tool(
            session,
            "list_recordings",
            {"user_id": self.user_id, "token": self.token},
        )
        list_video = await self._call_tool(
            session,
            "list_videos",
            {"user_id": self.user_id, "token": self.token},
        )
        recordings = list_audio.get("recordings", [])
        videos = list_video.get("videos", [])

        steps.append(
            {
                "tool": "list_recordings",
                "input": {"user_id": self.user_id},
                "output_preview": f"Found {len(recordings)} recordings",
            }
        )
        steps.append(
            {
                "tool": "list_videos",
                "input": {"user_id": self.user_id},
                "output_preview": f"Found {len(videos)} videos",
            }
        )

        combined: list[tuple[str, str, int, str]] = []
        for r in recordings:
            combined.append((
                r.get("created_at", ""),
                "audio",
                r.get("id"),
                r.get("filename", ""),
            ))
        for v in videos:
            combined.append((
                v.get("created_at", ""),
                "video",
                v.get("id"),
                v.get("filename", ""),
            ))

        if not combined:
            return AgentResult(answer="No recordings or videos found.", steps=steps)

        combined.sort(key=lambda item: item[0], reverse=True)
        lines = [f"- [{kind}] #{obj_id} {name}" for _, kind, obj_id, name in combined[:10]]
        return AgentResult(answer="Recent media:\n" + "\n".join(lines), steps=steps)

    async def _search_media(
        self,
        session: ClientSession,
        query: str,
        steps: list[dict[str, Any]],
        wants_audio: bool,
        wants_video: bool,
    ) -> AgentResult:
        if wants_video and not wants_audio:
            search_result = await self._call_tool(
                session,
                "search_videos",
                {"query": query, "limit": 5, "token": self.token},
            )
            results = search_result.get("results", [])
            steps.append(
                {
                    "tool": "search_videos",
                    "input": {"query": query, "limit": 5},
                    "output_preview": f"Found {len(results)} matches",
                }
            )
            if not results:
                return AgentResult(answer="No matching videos found.", steps=steps)
            lines = [f"- [video] #{item['id']} {item['filename']}" for item in results]
            return AgentResult(answer="Matches:\n" + "\n".join(lines), steps=steps)

        if wants_audio and not wants_video:
            search_result = await self._call_tool(
                session,
                "search_recordings",
                {"query": query, "limit": 5, "token": self.token},
            )
            results = search_result.get("results", [])
            steps.append(
                {
                    "tool": "search_recordings",
                    "input": {"query": query, "limit": 5},
                    "output_preview": f"Found {len(results)} matches",
                }
            )
            if not results:
                return AgentResult(answer="No matching recordings found.", steps=steps)
            lines = [f"- [audio] #{item['id']} {item['filename']}" for item in results]
            return AgentResult(answer="Matches:\n" + "\n".join(lines), steps=steps)

        audio_results = await self._call_tool(
            session,
            "search_recordings",
            {"query": query, "limit": 3, "token": self.token},
        )
        video_results = await self._call_tool(
            session,
            "search_videos",
            {"query": query, "limit": 3, "token": self.token},
        )
        audios = audio_results.get("results", [])
        videos = video_results.get("results", [])
        steps.append(
            {
                "tool": "search_recordings",
                "input": {"query": query, "limit": 3},
                "output_preview": f"Found {len(audios)} matches",
            }
        )
        steps.append(
            {
                "tool": "search_videos",
                "input": {"query": query, "limit": 3},
                "output_preview": f"Found {len(videos)} matches",
            }
        )

        if not audios and not videos:
            return AgentResult(answer="No matching media found.", steps=steps)

        lines = [f"- [audio] #{item['id']} {item['filename']}" for item in audios]
        lines.extend([f"- [video] #{item['id']} {item['filename']}" for item in videos])
        return AgentResult(answer="Matches:\n" + "\n".join(lines), steps=steps)

    async def _call_tool(
        self,
        session: ClientSession,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        response = await session.call_tool(tool_name, arguments=arguments)
        if not response.content:
            return {}
        first = response.content[0]
        text = getattr(first, "text", "{}")
        try:
            import json

            return json.loads(text)
        except Exception:
            return {"raw": text}

    def _session(self):
        return _MCPContext(self)


class _MCPContext:
    def __init__(self, parent: RecordingMCPAgent):
        self.parent = parent
        self._stdio_cm = None
        self._session = None

    async def __aenter__(self):
        command = os.getenv("MCP_SERVER_COMMAND")
        if not command:
            raise RuntimeError("Set MCP_SERVER_COMMAND for agent execution.")
        args = os.getenv("MCP_SERVER_ARGS", "").strip()
        server_params = StdioServerParameters(
            command=command,
            args=args.split() if args else [],
            env={
                **os.environ,
                "MCP_API_TOKEN": self.parent.token or os.getenv("MCP_API_TOKEN", ""),
            },
        )
        self._stdio_cm = stdio_client(server_params)
        read, write = await self._stdio_cm.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc, tb)
        if self._stdio_cm:
            await self._stdio_cm.__aexit__(exc_type, exc, tb)


def run_agent_sync(query: str, user_id: int, token: str | None = None) -> AgentResult:
    agent = RecordingMCPAgent(user_id=user_id, token=token)
    return asyncio.run(agent.run(query))

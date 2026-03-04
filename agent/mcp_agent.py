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

        async with self._session() as session:
            if "latest recording" in normalized or "last recording" in normalized:
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

                latest = recordings[0]
                recording_id = latest["id"]

                if "summarize" in normalized or "summary" in normalized:
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

                return AgentResult(
                    answer=f"Latest recording: #{recording_id} {latest['filename']}",
                    steps=steps,
                )

            if "find" in normalized or "search" in normalized or "mention" in normalized:
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
                lines = [f"- #{item['id']} {item['filename']}" for item in results]
                return AgentResult(answer="Matches:\n" + "\n".join(lines), steps=steps)

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

    async def _call_tool(
        self, session: ClientSession, tool_name: str, arguments: dict[str, Any]
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

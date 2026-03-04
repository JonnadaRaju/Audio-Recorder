from pydantic import BaseModel
from datetime import datetime


class RecordingCreate(BaseModel):
    filename: str
    file_size: int
    duration: int | None = None


class RecordingResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_size: int
    duration: int | None
    transcript: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecordingListResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    duration: int | None
    transcript: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    recording_id: int
    transcript: str
    transcript_preview: str


class SearchRequest(BaseModel):
    query: str
    limit: int | None = None


class SearchResultItem(BaseModel):
    id: int
    filename: str
    duration: int | None
    created_at: datetime
    transcript_preview: str

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: list[SearchResultItem]


class SummaryResponse(BaseModel):
    recording_id: int
    summary: str


class RecordingQuestionRequest(BaseModel):
    question: str
    limit: int | None = None


class RecordingQuestionResponse(BaseModel):
    question: str
    answer: str
    matched_recording_ids: list[int]

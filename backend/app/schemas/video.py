from datetime import datetime

from pydantic import BaseModel


class VideoRecordingResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_size: int
    duration: int | None
    transcript: str | None = None
    summary: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoRecordingListResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    duration: int | None
    transcript: str | None = None
    summary: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoTranscriptResponse(BaseModel):
    video_id: int
    transcript: str
    transcript_preview: str


class VideoSummaryResponse(BaseModel):
    video_id: int
    summary: str


class VideoSearchRequest(BaseModel):
    query: str
    limit: int | None = None


class VideoSearchResultItem(BaseModel):
    id: int
    filename: str
    duration: int | None
    created_at: datetime
    transcript_preview: str

    class Config:
        from_attributes = True


class VideoSearchResponse(BaseModel):
    query: str
    total_matches: int
    results: list[VideoSearchResultItem]


class VideoQuestionRequest(BaseModel):
    question: str
    limit: int | None = None


class VideoQuestionResponse(BaseModel):
    question: str
    answer: str
    matched_video_ids: list[int]

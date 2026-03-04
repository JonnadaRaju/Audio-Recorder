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
    created_at: datetime

    class Config:
        from_attributes = True


class RecordingListResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    duration: int | None
    created_at: datetime

    class Config:
        from_attributes = True

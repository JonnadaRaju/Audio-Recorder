import mimetypes
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.video import (
    VideoQuestionRequest,
    VideoQuestionResponse,
    VideoRecordingListResponse,
    VideoRecordingResponse,
    VideoSearchRequest,
    VideoSearchResponse,
    VideoSearchResultItem,
    VideoSummaryResponse,
    VideoTranscriptResponse,
)
from app.services.ai_service import (
    AIServiceError,
    answer_question_with_groq,
    build_video_context_chunks,
    semantic_search_videos,
    summarize_and_store_video,
    transcribe_and_store_video,
)
from app.services.auth_service import get_current_user
from app.services.video_service import (
    create_video_recording,
    delete_video,
    get_video,
    get_videos,
    save_video_file,
)

router = APIRouter(prefix="/videos", tags=["Videos"])


ALLOWED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
}


@router.post("/upload", response_model=VideoRecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    duration: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    raw_content_type = (file.content_type or "").lower()
    content_type = raw_content_type.split(";")[0].strip()
    if not content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video files are allowed",
        )

    if content_type not in ALLOWED_VIDEO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported video format",
        )

    contents = await file.read()
    await file.close()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty files are not allowed",
        )

    max_size_bytes = settings.MAX_VIDEO_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_VIDEO_FILE_SIZE_MB}MB",
        )

    _, file_path = await save_video_file(contents, current_user.id, file.filename)
    display_filename = os.path.basename(file.filename) or "recording.webm"

    recording = await create_video_recording(
        db=db,
        user_id=current_user.id,
        filename=display_filename,
        file_path=file_path,
        file_size=file_size,
        duration=duration,
    )
    return recording


@router.get("", response_model=list[VideoRecordingListResponse])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_videos(db, current_user.id)


@router.get("/{video_id}", response_model=VideoRecordingResponse)
async def get_single_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await get_video(db, video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await get_video(db, video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    await delete_video(db, video)


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await get_video(db, video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server",
        )

    media_type = mimetypes.guess_type(video.filename)[0] or "video/mp4"
    return FileResponse(
        path=video.file_path,
        media_type=media_type,
        filename=video.filename,
    )


@router.post("/{video_id}/transcribe", response_model=VideoTranscriptResponse)
async def transcribe_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await get_video(db, video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    try:
        if not video.transcript:
            video = await transcribe_and_store_video(db, video)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    transcript_preview = video.transcript[:240] if video.transcript else ""
    return VideoTranscriptResponse(
        video_id=video.id,
        transcript=video.transcript or "",
        transcript_preview=transcript_preview,
    )


@router.post("/{video_id}/summarize", response_model=VideoSummaryResponse)
async def summarize_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = await get_video(db, video_id, current_user.id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    try:
        if not video.summary:
            video = await summarize_and_store_video(db, video)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return VideoSummaryResponse(video_id=video.id, summary=video.summary or "")


@router.post("/search", response_model=VideoSearchResponse)
async def search_videos(
    request: VideoSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        matches = await semantic_search_videos(
            db=db,
            user_id=current_user.id,
            query=request.query,
            limit=request.limit,
        )
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    results = [
        VideoSearchResultItem(
            id=video.id,
            filename=video.filename,
            duration=video.duration,
            created_at=video.created_at,
            transcript_preview=(video.transcript or "")[:240],
        )
        for video in matches
    ]

    return VideoSearchResponse(
        query=request.query,
        total_matches=len(results),
        results=results,
    )


@router.post("/answer", response_model=VideoQuestionResponse)
async def answer_question_about_videos(
    request: VideoQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        matches = await semantic_search_videos(
            db=db,
            user_id=current_user.id,
            query=request.question,
            limit=request.limit or 5,
        )
        context = build_video_context_chunks(matches)
        final_answer = answer_question_with_groq(request.question, context)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return VideoQuestionResponse(
        question=request.question,
        answer=final_answer,
        matched_video_ids=[video.id for video in matches],
    )

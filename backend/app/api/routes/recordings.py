import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User
from app.schemas.recording import (
    RecordingResponse,
    RecordingListResponse,
    TranscriptResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SummaryResponse,
    RecordingQuestionRequest,
    RecordingQuestionResponse,
)
from app.services.auth_service import get_current_user
from app.services.ai_service import (
    AIServiceError,
    transcribe_and_store_recording,
    semantic_search_recordings,
    summarize_text,
    answer_question,
    build_context_chunks,
)
from app.services.recording_service import (
    save_audio_file,
    create_recording,
    get_recordings,
    get_recording,
    delete_recording
)

router = APIRouter(prefix="/recordings", tags=["Recordings"])


@router.post("/upload", response_model=RecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    file: UploadFile = File(...),
    duration: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only audio files are allowed"
        )
    
    contents = await file.read()
    await file.close()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty files are not allowed"
        )
    
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    _, file_path = await save_audio_file(contents, current_user.id)
    display_filename = os.path.basename(file.filename) or "recording.webm"
    
    recording = await create_recording(
        db=db,
        user_id=current_user.id,
        filename=display_filename,
        file_path=file_path,
        file_size=file_size,
        duration=duration
    )
    return recording


@router.get("", response_model=list[RecordingListResponse])
async def list_recordings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recordings = await get_recordings(db, current_user.id)
    return recordings


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_single_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recording = await get_recording(db, recording_id, current_user.id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    return recording


@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recording = await get_recording(db, recording_id, current_user.id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    await delete_recording(db, recording)


@router.get("/{recording_id}/stream")
async def stream_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recording = await get_recording(db, recording_id, current_user.id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    if not os.path.exists(recording.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=recording.file_path,
        media_type="audio/webm",
        filename=recording.filename
    )


@router.post("/{recording_id}/transcribe", response_model=TranscriptResponse)
async def transcribe_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recording = await get_recording(db, recording_id, current_user.id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    try:
        if not recording.transcript:
            recording = await transcribe_and_store_recording(db, recording)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    transcript_preview = recording.transcript[:240] if recording.transcript else ""
    return TranscriptResponse(
        recording_id=recording.id,
        transcript=recording.transcript or "",
        transcript_preview=transcript_preview,
    )


@router.post("/search", response_model=SearchResponse)
async def search_recordings(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        matches = await semantic_search_recordings(
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
        SearchResultItem(
            id=recording.id,
            filename=recording.filename,
            duration=recording.duration,
            created_at=recording.created_at,
            transcript_preview=(recording.transcript or "")[:240],
        )
        for recording in matches
    ]

    return SearchResponse(
        query=request.query,
        total_matches=len(results),
        results=results,
    )


@router.post("/{recording_id}/summarize", response_model=SummaryResponse)
async def summarize_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recording = await get_recording(db, recording_id, current_user.id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    try:
        if not recording.transcript:
            recording = await transcribe_and_store_recording(db, recording)
        summary = summarize_text(recording.transcript or "")
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return SummaryResponse(recording_id=recording.id, summary=summary)


@router.post("/answer", response_model=RecordingQuestionResponse)
async def answer_question_about_recordings(
    request: RecordingQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        matches = await semantic_search_recordings(
            db=db,
            user_id=current_user.id,
            query=request.question,
            limit=request.limit or 5,
        )
        context = build_context_chunks(matches)
        final_answer = answer_question(request.question, context)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return RecordingQuestionResponse(
        question=request.question,
        answer=final_answer,
        matched_recording_ids=[recording.id for recording in matches],
    )

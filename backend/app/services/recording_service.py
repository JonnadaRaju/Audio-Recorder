import os
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.models import AudioRecording


async def save_audio_file(file_content: bytes, user_id: int) -> tuple[str, str]:
    upload_dir = Path(settings.UPLOAD_AUDIO_DIR or settings.UPLOAD_DIR) / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{uuid.uuid4()}.webm"
    file_path = upload_dir / filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return filename, str(file_path)


async def create_recording(
    db: AsyncSession,
    user_id: int,
    filename: str,
    file_path: str,
    file_size: int,
    duration: int | None = None
) -> AudioRecording:
    recording = AudioRecording(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        duration=duration
    )
    db.add(recording)
    await db.commit()
    await db.refresh(recording)
    return recording


async def get_recordings(db: AsyncSession, user_id: int) -> list[AudioRecording]:
    result = await db.execute(
        select(AudioRecording)
        .where(AudioRecording.user_id == user_id)
        .order_by(AudioRecording.created_at.desc())
    )
    return list(result.scalars().all())


async def get_recording(db: AsyncSession, recording_id: int, user_id: int) -> AudioRecording | None:
    result = await db.execute(
        select(AudioRecording)
        .where(AudioRecording.id == recording_id, AudioRecording.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete_recording(db: AsyncSession, recording: AudioRecording) -> None:
    if os.path.exists(recording.file_path):
        os.remove(recording.file_path)
    await db.delete(recording)
    await db.commit()

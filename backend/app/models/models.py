from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.config import settings
from app.core.database import Base

try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ModuleNotFoundError:
    Vector = None
    VECTOR_AVAILABLE = False


def _embedding_column_type():
    if settings.USE_PGVECTOR and VECTOR_AVAILABLE and Vector is not None:
        return Vector(1536)
    return JSON


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    provider = Column(String(50), nullable=True)
    provider_id = Column(String(255), nullable=True)
    provider_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    recordings = relationship("AudioRecording", back_populates="user")
    videos = relationship("VideoRecording", back_populates="user")


class AudioRecording(Base):
    __tablename__ = "audio_recordings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
    transcript_embedding = Column(_embedding_column_type(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recordings")


class VideoRecording(Base):
    __tablename__ = "video_recordings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
    transcript_embedding = Column(_embedding_column_type(), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="videos")

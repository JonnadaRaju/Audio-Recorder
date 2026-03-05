from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads/audio"  # Legacy audio path setting
    UPLOAD_AUDIO_DIR: str = "uploads/audio"
    UPLOAD_VIDEO_DIR: str = "uploads/videos"
    MAX_FILE_SIZE_MB: int = 50
    MAX_VIDEO_FILE_SIZE_MB: int = 500
    FFMPEG_BINARY: str = "ffmpeg"
    EXTRACTED_AUDIO_DIR: str = "uploads/extracted_audio"
    USE_LOCAL_WHISPER: bool = False
    LOCAL_WHISPER_MODEL: str = "small"
    LOCAL_WHISPER_DEVICE: str = "cpu"
    LOCAL_WHISPER_COMPUTE_TYPE: str = "int8"
    LOCAL_WHISPER_BEAM_SIZE: int = 5

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_TRANSCRIPTION_MODEL: str = "gpt-4o-mini-transcribe"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"

    TRANSCRIPTION_API_KEY: str | None = None
    TRANSCRIPTION_BASE_URL: str | None = None
    TRANSCRIPTION_MODEL: str | None = None

    SARVAM_API_KEY: str | None = None
    SARVAM_BASE_URL: str | None = None
    SARVAM_TRANSCRIPTION_MODEL: str | None = None
    SARVAM_TRANSCRIPTION_ENDPOINT: str = "/audio/transcriptions"

    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_MODEL: str | None = None

    CHAT_API_KEY: str | None = None
    CHAT_BASE_URL: str | None = None
    CHAT_MODEL: str | None = None

    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str | None = None
    OPENROUTER_MODEL: str | None = None
    GROQ_API_KEY: str | None = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    OPENROUTER_SITE_URL: str | None = None
    OPENROUTER_APP_NAME: str | None = None
    OPENROUTER_AUDIO_INPUT_MODEL: str = "openai/gpt-audio-mini"
    USE_PGVECTOR: bool = True
    DEFAULT_SUMMARY_MAX_WORDS: int = 120
    VECTOR_SEARCH_LIMIT: int = 10
    MIN_SEARCH_SIMILARITY: float = 0.2
    PROMPT_GUARD_MAX_QUERY_CHARS: int = 4000
    
    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
        extra = "allow"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

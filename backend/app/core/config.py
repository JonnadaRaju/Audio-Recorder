from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "uploads/audio"
    MAX_FILE_SIZE_MB: int = 50
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_TRANSCRIPTION_MODEL: str = "gpt-4o-mini-transcribe"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    TRANSCRIPTION_API_KEY: str | None = None
    TRANSCRIPTION_BASE_URL: str | None = None
    TRANSCRIPTION_MODEL: str | None = None
    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_MODEL: str | None = None
    CHAT_API_KEY: str | None = None
    CHAT_BASE_URL: str | None = None
    CHAT_MODEL: str | None = None
    OPENROUTER_SITE_URL: str | None = None
    OPENROUTER_APP_NAME: str | None = None
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

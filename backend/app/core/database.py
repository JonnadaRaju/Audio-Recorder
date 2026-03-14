from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _normalize_async_database_url(database_url: str) -> str:
    # Render commonly provides postgres:// or postgresql:// URLs.
    # This app uses SQLAlchemy async engine, so force asyncpg driver when missing.
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


engine = create_async_engine(_normalize_async_database_url(settings.DATABASE_URL), echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db():
    # Keep extension creation in a separate transaction so failure doesn't poison
    # metadata creation for users lacking CREATE EXTENSION privileges.
    if settings.USE_PGVECTOR and settings.DATABASE_URL.startswith("postgresql"):
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as exc:
                logger.warning("Could not enable pgvector extension: %s", exc)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Lightweight forward-compatible schema patch for existing deployments
    # that were created before AI/video columns were introduced.
    vector_type_available = False
    if settings.USE_PGVECTOR and settings.DATABASE_URL.startswith("postgresql"):
        async with engine.begin() as conn:
            try:
                result = await conn.execute(
                    text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector')")
                )
                vector_type_available = bool(result.scalar())
            except Exception as exc:
                logger.warning("Could not detect vector type availability: %s", exc)

    # Run each DDL statement in its own transaction to avoid a failed ALTER
    # leaving the transaction in an aborted state and rolling back prior steps.
    schema_patch_statements = [
        "ALTER TABLE audio_recordings ADD COLUMN IF NOT EXISTS transcript TEXT",
        "ALTER TABLE video_recordings ADD COLUMN IF NOT EXISTS transcript TEXT",
        "ALTER TABLE video_recordings ADD COLUMN IF NOT EXISTS summary TEXT",
        "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_email VARCHAR(255)",
    ]

    embedding_column_type = "VECTOR(1536)" if vector_type_available else "JSONB"
    schema_patch_statements.extend(
        [
            f"ALTER TABLE audio_recordings ADD COLUMN IF NOT EXISTS transcript_embedding {embedding_column_type}",
            f"ALTER TABLE video_recordings ADD COLUMN IF NOT EXISTS transcript_embedding {embedding_column_type}",
        ]
    )

    for statement in schema_patch_statements:
        async with engine.begin() as conn:
            try:
                await conn.execute(text(statement))
            except Exception as exc:
                logger.warning("Could not apply schema patch (%s): %s", statement, exc)

    if vector_type_available:
        conversion_statements = [
            """
            ALTER TABLE audio_recordings
            ALTER COLUMN transcript_embedding TYPE vector(1536)
            USING CASE
              WHEN transcript_embedding IS NULL THEN NULL
              ELSE transcript_embedding::text::vector
            END
            """,
            """
            ALTER TABLE video_recordings
            ALTER COLUMN transcript_embedding TYPE vector(1536)
            USING CASE
              WHEN transcript_embedding IS NULL THEN NULL
              ELSE transcript_embedding::text::vector
            END
            """,
        ]

        for statement in conversion_statements:
            async with engine.begin() as conn:
                try:
                    await conn.execute(text(statement))
                except Exception as exc:
                    logger.warning("Could not convert embeddings to vector (%s): %s", statement.strip(), exc)

        vector_index_statements = [
            (
                "CREATE INDEX IF NOT EXISTS idx_audio_recordings_transcript_embedding "
                "ON audio_recordings USING ivfflat (transcript_embedding vector_cosine_ops) "
                "WITH (lists = 100)"
            ),
            (
                "CREATE INDEX IF NOT EXISTS idx_video_recordings_transcript_embedding "
                "ON video_recordings USING ivfflat (transcript_embedding vector_cosine_ops) "
                "WITH (lists = 100)"
            ),
        ]

        for statement in vector_index_statements:
            async with engine.begin() as conn:
                try:
                    await conn.execute(text(statement))
                except Exception as exc:
                    logger.warning("Could not apply vector index patch (%s): %s", statement, exc)

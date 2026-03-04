from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db():
    # Keep extension creation in a separate transaction so failure doesn't poison
    # metadata creation for users lacking CREATE EXTENSION privileges.
    if settings.DATABASE_URL.startswith("postgresql"):
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as exc:
                logger.warning("Could not enable pgvector extension: %s", exc)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Lightweight forward-compatible schema patch for existing deployments
    # that were created before AI columns were introduced.
    if settings.DATABASE_URL.startswith("postgresql"):
        async with engine.begin() as conn:
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE audio_recordings "
                        "ADD COLUMN IF NOT EXISTS transcript TEXT"
                    )
                )
                await conn.execute(
                    text(
                        "ALTER TABLE audio_recordings "
                        "ADD COLUMN IF NOT EXISTS transcript_embedding VECTOR(1536)"
                    )
                )
            except Exception:
                try:
                    await conn.execute(
                        text(
                            "ALTER TABLE audio_recordings "
                            "ADD COLUMN IF NOT EXISTS transcript_embedding JSONB"
                        )
                    )
                except Exception as exc:
                    logger.warning("Could not patch AI columns on startup: %s", exc)

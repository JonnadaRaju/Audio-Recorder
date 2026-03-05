from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.api.routes import auth, recordings, videos, agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Audio and Video Recorder API",
    description="API for recording, storing, streaming, and understanding audio/video files",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    # Token auth is passed via Authorization header, not cookies.
    # Keeping credentials disabled allows wildcard CORS for simpler local/dev access.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(recordings.router)
app.include_router(videos.router)
app.include_router(agent.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from fastapi import APIRouter
from app.api.routes import auth, recordings, videos, agent

router = APIRouter()
router.include_router(auth.router)
router.include_router(recordings.router)
router.include_router(videos.router)
router.include_router(agent.router)

from fastapi import APIRouter
from app.api.routes import auth, recordings

router = APIRouter()
router.include_router(auth.router)
router.include_router(recordings.router)

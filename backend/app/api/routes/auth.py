from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.models.models import User
from app.schemas.user import LoginRequest, UserCreate, UserResponse, Token
from app.services.auth_service import create_access_token
from app.services.oauth_service import OAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class OAuthConfig(BaseModel):
    google_client_id: str | None = None
    github_client_id: str | None = None
    frontend_url: str | None = None


@router.get("/oauth/config", response_model=OAuthConfig)
async def get_oauth_config():
    """Get OAuth configuration (client IDs only, no secrets)"""
    return OAuthConfig(
        google_client_id=settings.GOOGLE_CLIENT_ID,
        github_client_id=settings.GITHUB_CLIENT_ID,
        frontend_url=settings.FRONTEND_URL
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/google/callback")
async def google_callback(code: str, state: str | None = None, db: AsyncSession = Depends(get_db)):
    """Callback endpoint for Google OAuth"""
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )
        
        # Exchange code for access token
        redirect_uri = f"{settings.FRONTEND_URL}/auth/google/callback"
        access_token = await OAuthService.get_google_access_token(code, redirect_uri)
        
        # Get user info from Google
        user_info = await OAuthService.get_google_user_info(access_token)
        
        # Get or create user
        user = await OAuthService.get_or_create_user_from_oauth(
            db=db,
            provider="google",
            provider_id=user_info["id"],
            email=user_info["email"],
            provider_email=user_info.get("email")
        )
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token
        return {"access_token": jwt_token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )


@router.get("/github/callback")
async def github_callback(code: str, state: str | None = None, db: AsyncSession = Depends(get_db)):
    """Callback endpoint for GitHub OAuth"""
    try:
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth not configured"
            )
        
        # Exchange code for access token
        access_token = await OAuthService.get_github_access_token(code)
        
        # Get user info from GitHub
        user_info = await OAuthService.get_github_user_info(access_token)
        email = user_info.get("email") or await OAuthService.get_github_user_email(access_token)
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to retrieve email from GitHub"
            )
        
        # Get or create user
        user = await OAuthService.get_or_create_user_from_oauth(
            db=db,
            provider="github",
            provider_id=str(user_info["id"]),
            email=email,
            provider_email=email
        )
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token
        return {"access_token": jwt_token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub authentication failed: {str(e)}"
        )

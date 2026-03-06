import httpx
import json
from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.models import User
from app.services.auth_service import create_access_token


class OAuthService:
    """Service for handling OAuth authentication with Google and GitHub"""

    @staticmethod
    async def get_or_create_user_from_oauth(
        db: AsyncSession, 
        provider: str, 
        provider_id: str, 
        email: str,
        provider_email: str | None = None
    ) -> User:
        """Get existing user or create new user from OAuth provider"""
        
        # Try to find user by provider_id
        result = await db.execute(
            select(User).where(
                (User.provider == provider) & (User.provider_id == provider_id)
            )
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Try to find user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            # Link OAuth account to existing user
            user.provider = provider
            user.provider_id = provider_id
            if provider_email:
                user.provider_email = provider_email
            await db.commit()
            await db.refresh(user)
            return user
        
        # Create new user
        user = User(
            email=email,
            provider=provider,
            provider_id=provider_id,
            provider_email=provider_email or email
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_google_user_info(access_token: str) -> dict:
        """Fetch user info from Google using access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_google_access_token(code: str, redirect_uri: str) -> str:
        """Exchange Google authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

    @staticmethod
    async def get_github_user_info(access_token: str) -> dict:
        """Fetch user info from GitHub using access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_github_user_email(access_token: str) -> str | None:
        """Fetch primary email from GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            response.raise_for_status()
            emails = response.json()
            # Find primary email
            for email_info in emails:
                if email_info.get("primary"):
                    return email_info.get("email")
            # Fall back to first verified email
            for email_info in emails:
                if email_info.get("verified"):
                    return email_info.get("email")
            # Return first email if no primary/verified
            return emails[0].get("email") if emails else None

    @staticmethod
    async def get_github_access_token(code: str) -> str:
        """Exchange GitHub authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from .database import get_db
from .models.user import User, UserRole
from .core.security import decode_token
from .core.exceptions import UnauthorizedException, ForbiddenException

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials (Bearer token)
        db: Database session

    Returns:
        Current user

    Raises:
        UnauthorizedException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Check token type
        if payload.get("type") != "access":
            raise UnauthorizedException(detail="Invalid token type")

        # Get user identifier from token
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise UnauthorizedException()

        # Try to parse as user ID (integer)
        try:
            user_id = int(user_identifier)
            stmt = select(User).where(User.id == user_id)
        except ValueError:
            # If not integer, treat as username
            stmt = select(User).where(User.username == user_identifier)

        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise UnauthorizedException(detail="User not found")

        if not user.is_active:
            raise UnauthorizedException(detail="User is inactive")

        return user

    except JWTError:
        raise UnauthorizedException(detail="Could not validate credentials")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        UnauthorizedException: If user is inactive
    """
    if not current_user.is_active:
        raise UnauthorizedException(detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current admin user

    Raises:
        ForbiddenException: If user is not admin
    """
    if not current_user.is_admin:
        raise ForbiddenException(detail="Admin access required")
    return current_user


async def get_current_manager_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current fleet manager or admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current manager user

    Raises:
        ForbiddenException: If user is not fleet manager or admin
    """
    if not (current_user.is_admin or current_user.is_fleet_manager):
        raise ForbiddenException(detail="Fleet manager or admin access required")
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function

    Example:
        @app.get("/admin-only", dependencies=[Depends(require_role([UserRole.ADMIN]))])
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles and not current_user.is_superuser:
            raise ForbiddenException(
                detail=f"Access denied. Required roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user

    return role_checker

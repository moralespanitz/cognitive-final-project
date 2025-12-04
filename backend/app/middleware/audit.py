"""
Audit middleware for automatic logging of admin actions.
"""

from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models.admin_log import AdminLog, LogLevel, ActionType


# Endpoints to audit (method -> resource_type mapping)
AUDITED_ENDPOINTS = {
    # User management
    ("POST", "/api/v1/users"): ("user", ActionType.CREATE),
    ("PUT", "/api/v1/users"): ("user", ActionType.UPDATE),
    ("DELETE", "/api/v1/users"): ("user", ActionType.DELETE),

    # Vehicle management
    ("POST", "/api/v1/vehicles"): ("vehicle", ActionType.CREATE),
    ("PUT", "/api/v1/vehicles"): ("vehicle", ActionType.UPDATE),
    ("DELETE", "/api/v1/vehicles"): ("vehicle", ActionType.DELETE),

    # Driver management
    ("POST", "/api/v1/drivers"): ("driver", ActionType.CREATE),
    ("PUT", "/api/v1/drivers"): ("driver", ActionType.UPDATE),
    ("DELETE", "/api/v1/drivers"): ("driver", ActionType.DELETE),

    # Trip management
    ("POST", "/api/v1/trips"): ("trip", ActionType.CREATE),
    ("PUT", "/api/v1/trips"): ("trip", ActionType.UPDATE),
    ("DELETE", "/api/v1/trips"): ("trip", ActionType.DELETE),

    # Device management
    ("POST", "/api/v1/devices"): ("device", ActionType.CREATE),
    ("PUT", "/api/v1/devices"): ("device", ActionType.UPDATE),
    ("DELETE", "/api/v1/devices"): ("device", ActionType.DELETE),

    # FAQ management
    ("POST", "/api/v1/faqs"): ("faq", ActionType.CREATE),
    ("PUT", "/api/v1/faqs"): ("faq", ActionType.UPDATE),
    ("DELETE", "/api/v1/faqs"): ("faq", ActionType.DELETE),

    # Authentication
    ("POST", "/api/v1/auth/login"): ("auth", ActionType.LOGIN),
    ("POST", "/api/v1/auth/logout"): ("auth", ActionType.LOGOUT),
}


def get_action_for_endpoint(method: str, path: str) -> Optional[tuple]:
    """
    Get the action type and resource for an endpoint.
    Returns (resource_type, action_type) or None if not audited.
    """
    # Check exact match first
    key = (method, path)
    if key in AUDITED_ENDPOINTS:
        return AUDITED_ENDPOINTS[key]

    # Check prefix match (for paths with IDs)
    for (ep_method, ep_path), action_info in AUDITED_ENDPOINTS.items():
        if method == ep_method and path.startswith(ep_path):
            return action_info

    return None


def extract_resource_id(path: str) -> Optional[int]:
    """Extract resource ID from path if present."""
    parts = path.split("/")
    for part in reversed(parts):
        try:
            return int(part)
        except ValueError:
            continue
    return None


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic audit logging of important actions."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process the request
        response = await call_next(request)

        # Only audit successful mutating requests
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return response

        if response.status_code >= 400:
            return response

        # Check if this endpoint should be audited
        action_info = get_action_for_endpoint(request.method, request.url.path)
        if not action_info:
            return response

        resource_type, action = action_info

        # Get user info from request state (set by auth dependency)
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)

        # Extract resource ID from path
        resource_id = extract_resource_id(request.url.path)

        # Create audit log entry
        try:
            async with AsyncSessionLocal() as db:
                log = AdminLog(
                    user_id=user_id,
                    username=username or "unknown",
                    action=action,
                    level=LogLevel.INFO,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    message=f"{action.value} {resource_type}" + (f" #{resource_id}" if resource_id else ""),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    endpoint=request.url.path,
                    method=request.method
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            # Don't fail the request if audit logging fails
            print(f"Audit logging failed: {e}")

        return response


class RequestStateMiddleware(BaseHTTPMiddleware):
    """Middleware to extract user info from JWT and store in request state."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Try to extract user info from authorization header
        auth_header = request.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from ..core.security import decode_token
                payload = decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                    try:
                        request.state.user_id = int(user_id)
                    except ValueError:
                        request.state.user_id = None
                    request.state.username = payload.get("username", user_id)
            except Exception:
                pass

        return await call_next(request)

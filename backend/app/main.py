"""
TaxiWatch FastAPI Application.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import engine, Base, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Create database tables (only for dev, use Alembic in production)
    if settings.DEBUG and settings.ENVIRONMENT == "development":
        logger.warning("Creating database tables (DEBUG mode)")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time taxi fleet monitoring with AI-powered incident detection",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


# Import and include routers
from .api.v1.auth import router as auth_router
from .api.v1.users import router as users_router
from .api.v1.vehicles import router as vehicles_router
from .api.v1.tracking import router as tracking_router
from .api.v1.video import router as video_router
from .api.v1.incidents import router as incidents_router
from .api.v1.chat import router as chat_router
from .api.v1.devices import router as devices_router
from .api.v1.faqs import router as faqs_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(vehicles_router, prefix="/api/v1", tags=["Vehicles"])
app.include_router(tracking_router, prefix="/api/v1/tracking", tags=["Tracking"])
app.include_router(video_router, prefix="/api/v1/video", tags=["Video"])
app.include_router(incidents_router, prefix="/api/v1", tags=["Incidents"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(faqs_router, prefix="/api/v1/faqs", tags=["FAQs"])


# WebSocket endpoint for real-time tracking
from fastapi import WebSocket, WebSocketDisconnect
from .websocket.tracking import tracking_manager

@app.websocket("/ws/tracking")
async def websocket_tracking_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time GPS tracking updates."""
    await tracking_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            # Could handle client messages here (e.g., subscribe to specific vehicles)
    except WebSocketDisconnect:
        tracking_manager.disconnect(websocket)


# SQLAdmin setup
# Commented out until admin/views.py is created
# if settings.DEBUG:
#     from sqladmin import Admin
#     from .admin.views import setup_admin_views
#
#     admin = Admin(app, engine.sync_engine if hasattr(engine, 'sync_engine') else None)
#     setup_admin_views(admin)
#     logger.info("SQLAdmin initialized at /admin")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )

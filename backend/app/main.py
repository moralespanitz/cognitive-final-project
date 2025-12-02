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
from .api.v1.chat import router as chat_router
from .api.v1.devices import router as devices_router
from .api.v1.faqs import router as faqs_router
from .api.v1.images import router as images_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(vehicles_router, prefix="/api/v1", tags=["Vehicles"])
app.include_router(tracking_router, prefix="/api/v1/tracking", tags=["Tracking"])
app.include_router(video_router, prefix="/api/v1/video", tags=["Video"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(faqs_router, prefix="/api/v1/faqs", tags=["FAQs"])
app.include_router(images_router, prefix="/api/v1/images", tags=["Trip Images"])


# WebSocket endpoints
from fastapi import WebSocket, WebSocketDisconnect
from .websocket.tracking import tracking_manager
from .websocket.video import video_manager
from .websocket.trips import trip_manager
from .api.v1.video import latest_frames
import asyncio


@app.websocket("/ws/tracking")
async def websocket_tracking_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time GPS tracking updates."""
    await tracking_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        tracking_manager.disconnect(websocket)


@app.websocket("/ws/video/{route_id}")
async def websocket_video_endpoint(websocket: WebSocket, route_id: str):
    """
    WebSocket endpoint for real-time video streaming.
    Frontend connects here to receive frames from ESP32-CAM devices.
    """
    await video_manager.connect(websocket, route_id)
    try:
        while True:
            # Send latest frame every 100ms if available
            if route_id in latest_frames:
                await websocket.send_json({
                    "type": "frame",
                    "route_id": route_id,
                    **latest_frames[route_id]
                })
            await asyncio.sleep(0.1)  # 10 FPS max
    except WebSocketDisconnect:
        video_manager.disconnect(websocket, route_id)


@app.websocket("/ws/trips/driver/{driver_id}")
async def websocket_driver_trips(websocket: WebSocket, driver_id: int):
    """
    WebSocket endpoint for drivers to receive real-time trip requests.
    All connected drivers will see new trip requests instantly.
    """
    await trip_manager.connect_driver(websocket, driver_id)
    try:
        while True:
            # Keep connection alive, waiting for messages
            data = await websocket.receive_text()
            # Handle any driver messages (e.g., acknowledgments)
    except WebSocketDisconnect:
        trip_manager.disconnect_driver(driver_id)


@app.websocket("/ws/trips/customer/{customer_id}")
async def websocket_customer_trips(websocket: WebSocket, customer_id: int):
    """
    WebSocket endpoint for customers to receive real-time trip updates.
    Customer will be notified when driver accepts, arrives, starts, completes trip.
    """
    await trip_manager.connect_customer(websocket, customer_id)
    try:
        while True:
            # Keep connection alive, waiting for messages
            data = await websocket.receive_text()
            # Handle any customer messages
    except WebSocketDisconnect:
        trip_manager.disconnect_customer(customer_id)


@app.get("/api/v1/trips/ws-stats")
async def get_trip_ws_stats():
    """Get WebSocket connection statistics for trips."""
    return trip_manager.get_stats()


# SQLAdmin setup
if settings.DEBUG:
    from sqladmin import Admin
    from .admin.views import setup_admin
    from sqlalchemy import create_engine

    # Create sync engine for SQLAdmin
    sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_database_url, echo=False)

    admin = Admin(app, sync_engine, title="TaxiWatch Admin")
    setup_admin(admin)
    logger.info("SQLAdmin initialized at /admin")


# AWS Lambda handler using Mangum
from mangum import Mangum
handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )

"""Pydantic schemas."""
from .user import UserCreate, UserUpdate, UserResponse, UserLogin
from .token import Token, TokenPayload
from .vehicle import DriverCreate, DriverUpdate, DriverResponse
from .vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from .vehicle import TripCreate, TripUpdate, TripResponse
from .tracking import GPSLocationCreate, GPSLocationResponse
from .video import VideoArchiveResponse, VideoStreamResponse
from .incident import IncidentCreate, IncidentResponse, AlertResponse
from .chat import ChatMessage, ChatResponse

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload",
    "DriverCreate", "DriverUpdate", "DriverResponse",
    "VehicleCreate", "VehicleUpdate", "VehicleResponse",
    "TripCreate", "TripUpdate", "TripResponse",
    "GPSLocationCreate", "GPSLocationResponse",
    "VideoArchiveResponse", "VideoStreamResponse",
    "IncidentCreate", "IncidentResponse", "AlertResponse",
    "ChatMessage", "ChatResponse",
]

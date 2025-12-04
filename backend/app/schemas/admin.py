"""
Pydantic schemas for admin endpoints (logs and stats).
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    """Action type enumeration."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    SYSTEM = "SYSTEM"


# ============== Admin Log Schemas ==============

class AdminLogBase(BaseModel):
    """Base schema for admin logs."""
    action: ActionType
    level: LogLevel = LogLevel.INFO
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class AdminLogCreate(AdminLogBase):
    """Schema for creating an admin log entry."""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


class AdminLogResponse(AdminLogBase):
    """Schema for admin log response."""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogListResponse(BaseModel):
    """Paginated list of admin logs."""
    items: List[AdminLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============== System Stats Schemas ==============

class TripStats(BaseModel):
    """Trip statistics."""
    total_trips: int = 0
    completed_trips: int = 0
    cancelled_trips: int = 0
    in_progress_trips: int = 0
    total_revenue: float = 0.0
    total_distance: float = 0.0
    average_fare: float = 0.0
    average_distance: float = 0.0
    average_duration_minutes: float = 0.0


class VehicleStats(BaseModel):
    """Vehicle statistics."""
    total_vehicles: int = 0
    active_vehicles: int = 0
    maintenance_vehicles: int = 0
    inactive_vehicles: int = 0
    utilization_rate: float = 0.0  # percentage of vehicles in use


class DriverStats(BaseModel):
    """Driver statistics."""
    total_drivers: int = 0
    on_duty_drivers: int = 0
    off_duty_drivers: int = 0
    busy_drivers: int = 0
    average_rating: float = 0.0
    average_trips_per_driver: float = 0.0


class UserStats(BaseModel):
    """User statistics."""
    total_users: int = 0
    active_users: int = 0
    admin_users: int = 0
    customer_users: int = 0
    driver_users: int = 0


class DeviceStats(BaseModel):
    """Device statistics."""
    total_devices: int = 0
    online_devices: int = 0
    offline_devices: int = 0
    error_devices: int = 0


class SystemHealthStats(BaseModel):
    """System health statistics."""
    database_connected: bool = True
    redis_connected: bool = True
    api_status: str = "healthy"
    uptime_seconds: float = 0.0
    last_check: datetime


class DashboardStatsResponse(BaseModel):
    """Complete dashboard statistics response."""
    trips: TripStats
    vehicles: VehicleStats
    drivers: DriverStats
    users: UserStats
    devices: DeviceStats
    system_health: SystemHealthStats
    generated_at: datetime


class RevenueByPeriod(BaseModel):
    """Revenue grouped by period."""
    period: str  # e.g., "2024-01", "2024-01-15", "Monday"
    revenue: float
    trip_count: int


class RevenueStatsResponse(BaseModel):
    """Revenue statistics response."""
    total_revenue: float
    revenue_by_period: List[RevenueByPeriod]
    period_type: str  # "daily", "weekly", "monthly"
    date_from: datetime
    date_to: datetime


# ============== Metric Schemas ==============

class SystemMetricBase(BaseModel):
    """Base schema for system metrics."""
    metric_name: str
    metric_type: str
    value: str
    unit: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class SystemMetricCreate(SystemMetricBase):
    """Schema for creating a system metric."""
    pass


class SystemMetricResponse(SystemMetricBase):
    """Schema for system metric response."""
    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True


# ============== Filter Schemas ==============

class LogFilterParams(BaseModel):
    """Filter parameters for log queries."""
    level: Optional[LogLevel] = None
    action: Optional[ActionType] = None
    resource_type: Optional[str] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


class StatsFilterParams(BaseModel):
    """Filter parameters for stats queries."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None

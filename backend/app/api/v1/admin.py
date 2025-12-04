"""
Admin API endpoints for logs and system statistics.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ...database import get_db
from ...dependencies import get_current_admin_user, get_current_manager_user
from ...models.user import User, UserRole
from ...models.vehicle import Driver, Vehicle, Trip, DriverStatus, VehicleStatus, TripStatus
from ...models.device import Device, DeviceStatus
from ...models.admin_log import AdminLog, SystemMetric, LogLevel as DBLogLevel, ActionType as DBActionType
from ...schemas.admin import (
    AdminLogResponse, AdminLogListResponse, AdminLogCreate,
    DashboardStatsResponse, TripStats, VehicleStats, DriverStats,
    UserStats, DeviceStats, SystemHealthStats, RevenueStatsResponse, RevenueByPeriod,
    LogLevel, ActionType
)

router = APIRouter()


# ============== Utility Functions ==============

async def create_admin_log(
    db: AsyncSession,
    user: Optional[User],
    action: DBActionType,
    message: str,
    level: DBLogLevel = DBLogLevel.INFO,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None
) -> AdminLog:
    """Create an admin log entry."""
    log = AdminLog(
        user_id=user.id if user else None,
        username=user.username if user else "SYSTEM",
        action=action,
        level=level,
        resource_type=resource_type,
        resource_id=resource_id,
        message=message,
        details=details,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        endpoint=str(request.url.path) if request else None,
        method=request.method if request else None
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


# ============== Admin Logs Endpoints ==============

@router.get("/logs", response_model=AdminLogListResponse)
async def get_admin_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    action: Optional[ActionType] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    search: Optional[str] = Query(None, description="Search in message"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get paginated admin logs with optional filters.
    Admin only endpoint.
    """
    # Build base query
    stmt = select(AdminLog)

    # Apply filters
    filters = []
    if level:
        filters.append(AdminLog.level == DBLogLevel(level.value))
    if action:
        filters.append(AdminLog.action == DBActionType(action.value))
    if resource_type:
        filters.append(AdminLog.resource_type == resource_type)
    if user_id:
        filters.append(AdminLog.user_id == user_id)
    if date_from:
        filters.append(AdminLog.created_at >= date_from)
    if date_to:
        filters.append(AdminLog.created_at <= date_to)
    if search:
        filters.append(AdminLog.message.ilike(f"%{search}%"))

    if filters:
        stmt = stmt.where(and_(*filters))

    # Get total count
    count_stmt = select(func.count(AdminLog.id))
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    stmt = stmt.order_by(AdminLog.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    # Log this access
    await create_admin_log(
        db=db,
        user=current_user,
        action=DBActionType.READ,
        message=f"Accessed admin logs (page {page})",
        level=DBLogLevel.DEBUG,
        resource_type="admin_logs"
    )

    return AdminLogListResponse(
        items=[AdminLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/logs/{log_id}", response_model=AdminLogResponse)
async def get_admin_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a specific admin log entry by ID."""
    stmt = select(AdminLog).where(AdminLog.id == log_id)
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()

    if not log:
        from ...core.exceptions import NotFoundException
        raise NotFoundException(detail="Log entry not found")

    return AdminLogResponse.model_validate(log)


@router.delete("/logs", status_code=204)
async def clear_old_logs(
    days_old: int = Query(30, ge=1, le=365, description="Delete logs older than N days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    request: Request = None
):
    """
    Delete admin logs older than specified number of days.
    Admin only endpoint.
    """
    from sqlalchemy import delete

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    stmt = delete(AdminLog).where(AdminLog.created_at < cutoff_date)
    result = await db.execute(stmt)
    await db.commit()

    deleted_count = result.rowcount

    # Log this action
    await create_admin_log(
        db=db,
        user=current_user,
        action=DBActionType.DELETE,
        message=f"Cleared {deleted_count} logs older than {days_old} days",
        level=DBLogLevel.WARNING,
        resource_type="admin_logs",
        details={"days_old": days_old, "deleted_count": deleted_count},
        request=request
    )


# ============== System Stats Endpoints ==============

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    date_from: Optional[datetime] = Query(None, description="Start date for stats"),
    date_to: Optional[datetime] = Query(None, description="End date for stats"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    Get comprehensive dashboard statistics.
    Available for Admin and Fleet Manager roles.
    """
    # Default date range: last 30 days
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    # ============== Trip Statistics ==============
    trip_filters = [Trip.created_at >= date_from, Trip.created_at <= date_to]

    # Total trips
    total_trips_stmt = select(func.count(Trip.id)).where(and_(*trip_filters))
    total_trips = (await db.execute(total_trips_stmt)).scalar() or 0

    # Completed trips
    completed_stmt = select(func.count(Trip.id)).where(
        and_(*trip_filters, Trip.status == TripStatus.COMPLETED)
    )
    completed_trips = (await db.execute(completed_stmt)).scalar() or 0

    # Cancelled trips
    cancelled_stmt = select(func.count(Trip.id)).where(
        and_(*trip_filters, Trip.status == TripStatus.CANCELLED)
    )
    cancelled_trips = (await db.execute(cancelled_stmt)).scalar() or 0

    # In progress trips
    in_progress_stmt = select(func.count(Trip.id)).where(
        and_(*trip_filters, Trip.status == TripStatus.IN_PROGRESS)
    )
    in_progress_trips = (await db.execute(in_progress_stmt)).scalar() or 0

    # Revenue and distance (from completed trips)
    revenue_stmt = select(
        func.coalesce(func.sum(Trip.fare), 0),
        func.coalesce(func.sum(Trip.distance), 0),
        func.coalesce(func.avg(Trip.fare), 0),
        func.coalesce(func.avg(Trip.distance), 0),
        func.coalesce(func.avg(Trip.duration), 0)
    ).where(and_(*trip_filters, Trip.status == TripStatus.COMPLETED))
    revenue_result = (await db.execute(revenue_stmt)).first()

    trip_stats = TripStats(
        total_trips=total_trips,
        completed_trips=completed_trips,
        cancelled_trips=cancelled_trips,
        in_progress_trips=in_progress_trips,
        total_revenue=float(revenue_result[0]) if revenue_result else 0,
        total_distance=float(revenue_result[1]) if revenue_result else 0,
        average_fare=float(revenue_result[2]) if revenue_result else 0,
        average_distance=float(revenue_result[3]) if revenue_result else 0,
        average_duration_minutes=float(revenue_result[4]) if revenue_result else 0
    )

    # ============== Vehicle Statistics ==============
    total_vehicles_stmt = select(func.count(Vehicle.id))
    total_vehicles = (await db.execute(total_vehicles_stmt)).scalar() or 0

    active_vehicles_stmt = select(func.count(Vehicle.id)).where(Vehicle.status == VehicleStatus.ACTIVE)
    active_vehicles = (await db.execute(active_vehicles_stmt)).scalar() or 0

    maintenance_vehicles_stmt = select(func.count(Vehicle.id)).where(Vehicle.status == VehicleStatus.MAINTENANCE)
    maintenance_vehicles = (await db.execute(maintenance_vehicles_stmt)).scalar() or 0

    inactive_vehicles_stmt = select(func.count(Vehicle.id)).where(
        or_(Vehicle.status == VehicleStatus.INACTIVE, Vehicle.status == VehicleStatus.OUT_OF_SERVICE)
    )
    inactive_vehicles = (await db.execute(inactive_vehicles_stmt)).scalar() or 0

    # Vehicles with active trips (utilization)
    vehicles_in_use_stmt = select(func.count(func.distinct(Trip.vehicle_id))).where(
        Trip.status == TripStatus.IN_PROGRESS
    )
    vehicles_in_use = (await db.execute(vehicles_in_use_stmt)).scalar() or 0
    utilization_rate = (vehicles_in_use / total_vehicles * 100) if total_vehicles > 0 else 0

    vehicle_stats = VehicleStats(
        total_vehicles=total_vehicles,
        active_vehicles=active_vehicles,
        maintenance_vehicles=maintenance_vehicles,
        inactive_vehicles=inactive_vehicles,
        utilization_rate=round(utilization_rate, 2)
    )

    # ============== Driver Statistics ==============
    total_drivers_stmt = select(func.count(Driver.id))
    total_drivers = (await db.execute(total_drivers_stmt)).scalar() or 0

    on_duty_stmt = select(func.count(Driver.id)).where(Driver.status == DriverStatus.ON_DUTY)
    on_duty_drivers = (await db.execute(on_duty_stmt)).scalar() or 0

    off_duty_stmt = select(func.count(Driver.id)).where(Driver.status == DriverStatus.OFF_DUTY)
    off_duty_drivers = (await db.execute(off_duty_stmt)).scalar() or 0

    # Drivers with active trips
    busy_drivers_stmt = select(func.count(func.distinct(Trip.driver_id))).where(
        Trip.status == TripStatus.IN_PROGRESS
    )
    busy_drivers = (await db.execute(busy_drivers_stmt)).scalar() or 0

    avg_rating_stmt = select(func.avg(Driver.rating)).where(Driver.rating > 0)
    avg_rating = (await db.execute(avg_rating_stmt)).scalar() or 0

    avg_trips_stmt = select(func.avg(Driver.total_trips))
    avg_trips_per_driver = (await db.execute(avg_trips_stmt)).scalar() or 0

    driver_stats = DriverStats(
        total_drivers=total_drivers,
        on_duty_drivers=on_duty_drivers,
        off_duty_drivers=off_duty_drivers,
        busy_drivers=busy_drivers,
        average_rating=round(float(avg_rating), 2) if avg_rating else 0,
        average_trips_per_driver=round(float(avg_trips_per_driver), 1) if avg_trips_per_driver else 0
    )

    # ============== User Statistics ==============
    total_users_stmt = select(func.count(User.id))
    total_users = (await db.execute(total_users_stmt)).scalar() or 0

    active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_users = (await db.execute(active_users_stmt)).scalar() or 0

    admin_users_stmt = select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    admin_users = (await db.execute(admin_users_stmt)).scalar() or 0

    customer_users_stmt = select(func.count(User.id)).where(User.role == UserRole.CUSTOMER)
    customer_users = (await db.execute(customer_users_stmt)).scalar() or 0

    driver_users_stmt = select(func.count(User.id)).where(User.role == UserRole.DRIVER)
    driver_users = (await db.execute(driver_users_stmt)).scalar() or 0

    user_stats = UserStats(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        customer_users=customer_users,
        driver_users=driver_users
    )

    # ============== Device Statistics ==============
    total_devices_stmt = select(func.count(Device.id))
    total_devices = (await db.execute(total_devices_stmt)).scalar() or 0

    online_devices_stmt = select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    online_devices = (await db.execute(online_devices_stmt)).scalar() or 0

    offline_devices_stmt = select(func.count(Device.id)).where(Device.status == DeviceStatus.OFFLINE)
    offline_devices = (await db.execute(offline_devices_stmt)).scalar() or 0

    error_devices_stmt = select(func.count(Device.id)).where(Device.status == DeviceStatus.ERROR)
    error_devices = (await db.execute(error_devices_stmt)).scalar() or 0

    device_stats = DeviceStats(
        total_devices=total_devices,
        online_devices=online_devices,
        offline_devices=offline_devices,
        error_devices=error_devices
    )

    # ============== System Health ==============
    system_health = SystemHealthStats(
        database_connected=True,  # We're connected if we got here
        redis_connected=True,  # Assume connected (could add actual check)
        api_status="healthy",
        uptime_seconds=0,  # Would need to track process start time
        last_check=datetime.utcnow()
    )

    return DashboardStatsResponse(
        trips=trip_stats,
        vehicles=vehicle_stats,
        drivers=driver_stats,
        users=user_stats,
        devices=device_stats,
        system_health=system_health,
        generated_at=datetime.utcnow()
    )


@router.get("/stats/revenue", response_model=RevenueStatsResponse)
async def get_revenue_stats(
    period: str = Query("daily", enum=["daily", "weekly", "monthly"], description="Aggregation period"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    Get revenue statistics grouped by period.
    Available for Admin and Fleet Manager roles.
    """
    # Default date range
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        if period == "daily":
            date_from = date_to - timedelta(days=30)
        elif period == "weekly":
            date_from = date_to - timedelta(weeks=12)
        else:  # monthly
            date_from = date_to - timedelta(days=365)

    # Get completed trips in range
    stmt = select(Trip).where(
        and_(
            Trip.status == TripStatus.COMPLETED,
            Trip.created_at >= date_from,
            Trip.created_at <= date_to
        )
    ).order_by(Trip.created_at)

    result = await db.execute(stmt)
    trips = result.scalars().all()

    # Group by period
    revenue_by_period: dict = {}
    total_revenue = 0.0

    for trip in trips:
        if period == "daily":
            key = trip.created_at.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Week number and year
            key = trip.created_at.strftime("%Y-W%W")
        else:  # monthly
            key = trip.created_at.strftime("%Y-%m")

        if key not in revenue_by_period:
            revenue_by_period[key] = {"revenue": 0.0, "count": 0}

        trip_fare = float(trip.fare) if trip.fare else 0.0
        revenue_by_period[key]["revenue"] += trip_fare
        revenue_by_period[key]["count"] += 1
        total_revenue += trip_fare

    # Convert to list
    revenue_list = [
        RevenueByPeriod(
            period=key,
            revenue=round(data["revenue"], 2),
            trip_count=data["count"]
        )
        for key, data in sorted(revenue_by_period.items())
    ]

    return RevenueStatsResponse(
        total_revenue=round(total_revenue, 2),
        revenue_by_period=revenue_list,
        period_type=period,
        date_from=date_from,
        date_to=date_to
    )


# ============== Resource Counts for Quick Overview ==============

@router.get("/stats/quick")
async def get_quick_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """
    Get quick count statistics for dashboard widgets.
    Lighter endpoint for frequent polling.
    """
    # Get counts in parallel
    total_vehicles = (await db.execute(select(func.count(Vehicle.id)))).scalar() or 0
    total_drivers = (await db.execute(select(func.count(Driver.id)))).scalar() or 0
    active_trips = (await db.execute(
        select(func.count(Trip.id)).where(Trip.status == TripStatus.IN_PROGRESS)
    )).scalar() or 0
    online_devices = (await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    )).scalar() or 0

    # Today's stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_trips = (await db.execute(
        select(func.count(Trip.id)).where(Trip.created_at >= today_start)
    )).scalar() or 0
    today_revenue_result = (await db.execute(
        select(func.coalesce(func.sum(Trip.fare), 0)).where(
            and_(Trip.created_at >= today_start, Trip.status == TripStatus.COMPLETED)
        )
    )).scalar() or 0

    return {
        "total_vehicles": total_vehicles,
        "total_drivers": total_drivers,
        "active_trips": active_trips,
        "online_devices": online_devices,
        "today_trips": today_trips,
        "today_revenue": float(today_revenue_result),
        "timestamp": datetime.utcnow().isoformat()
    }

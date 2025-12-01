"""
Incidents and Alerts API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ...database import get_db
from ...models.user import User
from ...models.incident import Incident, Alert
from ...schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse,
    AlertResponse, AlertAcknowledge
)
from ...dependencies import get_current_user
from ...core.exceptions import NotFoundException

router = APIRouter()


# Incident Endpoints
@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new incident."""
    db_incident = Incident(**incident_data.model_dump())
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)

    return db_incident


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    skip: int = 0,
    limit: int = 50,
    vehicle_id: int = None,
    driver_id: int = None,
    severity: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List incidents with filters."""
    stmt = select(Incident)

    if vehicle_id:
        stmt = stmt.where(Incident.vehicle_id == vehicle_id)
    if driver_id:
        stmt = stmt.where(Incident.driver_id == driver_id)
    if severity:
        stmt = stmt.where(Incident.severity == severity)

    stmt = stmt.offset(skip).limit(limit).order_by(Incident.detected_at.desc())
    result = await db.execute(stmt)
    incidents = result.scalars().all()

    return incidents


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get incident by ID."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise NotFoundException(detail="Incident not found")

    return incident


@router.put("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: int,
    resolution_notes: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an incident."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise NotFoundException(detail="Incident not found")

    incident.resolved_at = datetime.utcnow()
    incident.resolved_by_id = current_user.id
    incident.resolution_notes = resolution_notes

    await db.commit()
    await db.refresh(incident)

    return incident


# Alert Endpoints
@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 50,
    unacknowledged: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List alerts."""
    stmt = select(Alert)

    if unacknowledged:
        stmt = stmt.where(Alert.acknowledged == False)

    stmt = stmt.offset(skip).limit(limit).order_by(Alert.created_at.desc())
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    return alerts


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise NotFoundException(detail="Alert not found")

    alert.acknowledged = True
    alert.acknowledged_by_id = current_user.id
    alert.acknowledged_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return alert

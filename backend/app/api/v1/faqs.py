"""
FAQ API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from ...database import get_db
from ...models.user import User
from ...models.faq import FAQ, FAQCategory
from ...schemas.faq import FAQResponse, FAQCreate, FAQUpdate
from ...dependencies import get_current_user
from ...core.exceptions import NotFoundException

router = APIRouter()


@router.get("", response_model=List[FAQResponse])
async def list_faqs(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List FAQs (no auth required for public access)."""
    stmt = select(FAQ).where(FAQ.is_active == True)

    if category:
        try:
            category_enum = FAQCategory[category.upper()]
            stmt = stmt.where(FAQ.category == category_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid category")

    stmt = stmt.order_by(FAQ.priority.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    faqs = result.scalars().all()

    return faqs


@router.get("/{faq_id}", response_model=FAQResponse)
async def get_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get FAQ by ID."""
    stmt = select(FAQ).where(FAQ.id == faq_id)
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()

    if not faq:
        raise NotFoundException(detail="FAQ not found")

    return faq


@router.post("", response_model=FAQResponse, status_code=201)
async def create_faq(
    faq_data: FAQCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new FAQ (admin only)."""
    if current_user.role != "ADMIN" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    faq = FAQ(**faq_data.model_dump())
    db.add(faq)
    await db.commit()
    await db.refresh(faq)

    return faq


@router.patch("/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    faq_data: FAQUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update FAQ (admin only)."""
    if current_user.role != "ADMIN" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(FAQ).where(FAQ.id == faq_id)
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()

    if not faq:
        raise NotFoundException(detail="FAQ not found")

    # Update fields
    for field, value in faq_data.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)

    await db.commit()
    await db.refresh(faq)

    return faq


@router.delete("/{faq_id}", status_code=204)
async def delete_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete FAQ (admin only)."""
    if current_user.role != "ADMIN" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(FAQ).where(FAQ.id == faq_id)
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()

    if not faq:
        raise NotFoundException(detail="FAQ not found")

    await db.delete(faq)
    await db.commit()

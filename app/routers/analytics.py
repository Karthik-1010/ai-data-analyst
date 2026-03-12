from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user
from app.services.analytics_service import (
    get_summary_stats,
    get_department_breakdown,
    get_monthly_trends,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """KPI summary cards: total records, avg salary, avg performance score."""
    user_id = None if current_user.role == "admin" else current_user.id
    stats = await get_summary_stats(db, user_id)
    return stats


@router.get("/by-department")
async def by_department(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-department breakdown for bar/pie charts."""
    user_id = None if current_user.role == "admin" else current_user.id
    data = await get_department_breakdown(db, user_id)
    return data


@router.get("/trends")
async def trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Monthly trend data for line charts."""
    user_id = None if current_user.role == "admin" else current_user.id
    data = await get_monthly_trends(db, user_id)
    return data

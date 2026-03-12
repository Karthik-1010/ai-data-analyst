from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.data_record import DataRecord
from typing import Optional


async def get_summary_stats(db: AsyncSession, user_id: Optional[int] = None) -> dict:
    """Get KPI summary: total records, avg salary, avg performance score."""
    query = select(
        func.count(DataRecord.id).label("total_records"),
        func.avg(DataRecord.salary).label("avg_salary"),
        func.avg(DataRecord.performance_score).label("avg_score"),
        func.sum(DataRecord.salary).label("total_salary"),
    )
    if user_id:
        query = query.where(DataRecord.user_id == user_id)

    result = await db.execute(query)
    row = result.one()
    return {
        "total_records": row.total_records or 0,
        "avg_salary": round(float(row.avg_salary or 0), 2),
        "avg_score": round(float(row.avg_score or 0), 2),
        "total_salary": round(float(row.total_salary or 0), 2),
    }


async def get_department_breakdown(db: AsyncSession, user_id: Optional[int] = None) -> list:
    """Get per-department stats: count, avg salary, avg score."""
    query = select(
        DataRecord.department,
        func.count(DataRecord.id).label("count"),
        func.avg(DataRecord.salary).label("avg_salary"),
        func.avg(DataRecord.performance_score).label("avg_score"),
    ).group_by(DataRecord.department)

    if user_id:
        query = query.where(DataRecord.user_id == user_id)

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "department": row.department,
            "count": row.count,
            "avg_salary": round(float(row.avg_salary or 0), 2),
            "avg_score": round(float(row.avg_score or 0), 2),
        }
        for row in rows
    ]


async def get_monthly_trends(db: AsyncSession, user_id: Optional[int] = None) -> list:
    """Get monthly aggregations for line chart trends."""
    # Use substr to extract year-month from record_date
    month_expr = func.substr(func.cast(DataRecord.record_date, String), 1, 7)

    query = select(
        month_expr.label("month"),
        func.count(DataRecord.id).label("count"),
        func.avg(DataRecord.salary).label("avg_salary"),
        func.avg(DataRecord.performance_score).label("avg_score"),
    ).group_by(month_expr).order_by(month_expr)

    if user_id:
        query = query.where(DataRecord.user_id == user_id)

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "month": row.month,
            "count": row.count,
            "avg_salary": round(float(row.avg_salary or 0), 2),
            "avg_score": round(float(row.avg_score or 0), 2),
        }
        for row in rows
    ]


# Need String import for func.cast
from sqlalchemy import String

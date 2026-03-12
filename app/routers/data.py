from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import pandas as pd
import io
from app.database import get_db
from app.models.user import User
from app.models.data_record import DataRecord
from app.schemas.data_record import (
    DataRecordCreate,
    DataRecordUpdate,
    DataRecordResponse,
    DataRecordListResponse,
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/data", tags=["Data Records"])


@router.get("/", response_model=DataRecordListResponse)
async def list_records(
    skip: int = 0,
    limit: int = 50,
    department: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List data records. Admins see all; users see only their own."""
    query = select(DataRecord)

    # RBAC: filter by user_id for non-admins
    if current_user.role != "admin":
        query = query.where(DataRecord.user_id == current_user.id)

    # Optional department filter
    if department:
        query = query.where(DataRecord.department == department)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.order_by(DataRecord.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return DataRecordListResponse(
        records=[DataRecordResponse.model_validate(r) for r in records],
        total=total,
    )


@router.get("/export/excel", response_class=StreamingResponse)
async def export_excel(
    department: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export data records to an Excel file."""
    query = select(DataRecord)

    # RBAC: filter by user_id for non-admins
    if current_user.role != "admin":
        query = query.where(DataRecord.user_id == current_user.id)

    # Optional department filter
    if department:
        query = query.where(DataRecord.department == department)

    query = query.order_by(DataRecord.created_at.desc())
    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        raise HTTPException(status_code=404, detail="No records found to export")

    # Convert to list of dictionaries
    data = []
    for r in records:
        data.append({
            "Employee Name": r.employee_name,
            "Department": r.department,
            "Salary": r.salary,
            "Performance Score": r.performance_score,
            "Record Date": r.record_date,
        })

    df = pd.DataFrame(data)

    # Create an in-memory output file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data Records")

    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="data_records.xlsx"'
    }

    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



@router.post("/", response_model=DataRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    data: DataRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new data record."""
    record = DataRecord(
        user_id=current_user.id,
        employee_name=data.employee_name,
        department=data.department,
        salary=data.salary,
        performance_score=data.performance_score,
        record_date=data.record_date,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return DataRecordResponse.model_validate(record)


@router.get("/{record_id}", response_model=DataRecordResponse)
async def get_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single record by ID."""
    result = await db.execute(select(DataRecord).where(DataRecord.id == record_id))
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # RBAC: non-admins can only view their own records
    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return DataRecordResponse.model_validate(record)


@router.put("/{record_id}", response_model=DataRecordResponse)
async def update_record(
    record_id: int,
    data: DataRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a data record."""
    result = await db.execute(select(DataRecord).where(DataRecord.id == record_id))
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    await db.flush()
    await db.refresh(record)
    return DataRecordResponse.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a data record."""
    result = await db.execute(select(DataRecord).where(DataRecord.id == record_id))
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(record)

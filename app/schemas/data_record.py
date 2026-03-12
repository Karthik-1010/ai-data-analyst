from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


# --- Request Schemas ---

class DataRecordCreate(BaseModel):
    employee_name: str = Field(..., min_length=1, max_length=255, examples=["Jane Smith"])
    department: str = Field(..., min_length=1, max_length=100, examples=["Engineering"])
    salary: float = Field(..., gt=0, examples=[85000.0])
    performance_score: float = Field(..., ge=0, le=100, examples=[87.5])
    record_date: date = Field(..., examples=["2025-01-15"])


class DataRecordUpdate(BaseModel):
    employee_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    salary: Optional[float] = Field(None, gt=0)
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    record_date: Optional[date] = None


# --- Response Schemas ---

class DataRecordResponse(BaseModel):
    id: int
    user_id: int
    employee_name: str
    department: str
    salary: float
    performance_score: float
    record_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class DataRecordListResponse(BaseModel):
    records: List[DataRecordResponse]
    total: int

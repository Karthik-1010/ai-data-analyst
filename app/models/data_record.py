from datetime import datetime, date
from sqlalchemy import String, Float, Date, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DataRecord(Base):
    __tablename__ = "data_records"
    __table_args__ = (
        CheckConstraint("performance_score >= 0 AND performance_score <= 100", name="check_score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="data_records")

    def __repr__(self) -> str:
        return f"<DataRecord(id={self.id}, employee={self.employee_name}, dept={self.department})>"

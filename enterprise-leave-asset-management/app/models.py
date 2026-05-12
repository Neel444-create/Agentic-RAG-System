from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role(str, Enum):
    ADMIN = "admin"
    HR = "hr"
    EMPLOYEE = "employee"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AssetStatus(str, Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RETIRED = "retired"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    department: Mapped[str] = mapped_column(String(80), index=True)
    designation: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(SqlEnum(Role), default=Role.EMPLOYEE, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    leave_balance: Mapped[int] = mapped_column(Integer, default=24)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        back_populates="employee", foreign_keys="LeaveRequest.employee_id"
    )
    asset_requests: Mapped[list["AssetRequest"]] = relationship(
        back_populates="employee", foreign_keys="AssetRequest.employee_id"
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    leave_type: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[RequestStatus] = mapped_column(SqlEnum(RequestStatus), default=RequestStatus.PENDING, index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employee: Mapped[Employee] = relationship(back_populates="leave_requests", foreign_keys=[employee_id])
    reviewer: Mapped[Employee | None] = relationship(foreign_keys=[reviewer_id])


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_tag: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    model: Mapped[str] = mapped_column(String(120))
    status: Mapped[AssetStatus] = mapped_column(SqlEnum(AssetStatus), default=AssetStatus.AVAILABLE, index=True)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assigned_to: Mapped[Employee | None] = relationship(foreign_keys=[assigned_to_id])
    requests: Mapped[list["AssetRequest"]] = relationship(back_populates="asset")


class AssetRequest(Base):
    __tablename__ = "asset_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    business_justification: Mapped[str] = mapped_column(Text)
    status: Mapped[RequestStatus] = mapped_column(SqlEnum(RequestStatus), default=RequestStatus.PENDING, index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employee: Mapped[Employee] = relationship(back_populates="asset_requests", foreign_keys=[employee_id])
    asset: Mapped[Asset] = relationship(back_populates="requests")
    reviewer: Mapped[Employee | None] = relationship(foreign_keys=[reviewer_id])

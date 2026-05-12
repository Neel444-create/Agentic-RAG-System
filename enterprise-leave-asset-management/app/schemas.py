from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import AssetStatus, RequestStatus, Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmployeeBase(BaseModel):
    employee_code: str = Field(min_length=3, max_length=32)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    department: str = Field(min_length=2, max_length=80)
    designation: str = Field(min_length=2, max_length=120)
    role: Role = Role.EMPLOYEE


class EmployeeCreate(EmployeeBase):
    password: str = Field(min_length=8)
    leave_balance: int = Field(default=24, ge=0, le=60)


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    leave_balance: int
    created_at: datetime


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    leave_type: str = Field(min_length=2, max_length=40)
    reason: str = Field(min_length=5, max_length=500)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class DecisionUpdate(BaseModel):
    status: RequestStatus
    reviewer_comment: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def validate_terminal_status(self):
        if self.status == RequestStatus.PENDING:
            raise ValueError("decision status must be approved or rejected")
        return self


class LeaveRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str
    status: RequestStatus
    reviewer_id: int | None
    reviewer_comment: str | None
    created_at: datetime
    updated_at: datetime


class AssetCreate(BaseModel):
    asset_tag: str = Field(min_length=3, max_length=40)
    category: str = Field(min_length=2, max_length=60)
    model: str = Field(min_length=2, max_length=120)
    status: AssetStatus = AssetStatus.AVAILABLE


class AssetRead(AssetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_to_id: int | None
    created_at: datetime


class AssetRequestCreate(BaseModel):
    asset_id: int
    business_justification: str = Field(min_length=10, max_length=500)


class AssetRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    asset_id: int
    business_justification: str
    status: RequestStatus
    reviewer_id: int | None
    reviewer_comment: str | None
    created_at: datetime
    updated_at: datetime

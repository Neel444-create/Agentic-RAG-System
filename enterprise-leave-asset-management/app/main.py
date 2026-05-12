import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Asset, AssetRequest, AssetStatus, Employee, LeaveRequest, RequestStatus, Role
from .schemas import (
    AssetCreate,
    AssetRead,
    AssetRequestCreate,
    AssetRequestRead,
    DecisionUpdate,
    EmployeeCreate,
    EmployeeRead,
    LeaveRequestCreate,
    LeaveRequestRead,
    LoginRequest,
    Token,
)
from .security import create_access_token, get_current_user, hash_password, require_roles, verify_password

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield


app = FastAPI(
    title=os.getenv("APP_NAME", "Infosys Enterprise Leave & Asset Portal"),
    version="1.0.0",
    description="RBAC-enabled employee leave and IT asset management API for enterprise portfolio demos.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed_demo_data() -> None:
    db = next(get_db())
    try:
        if db.scalar(select(Employee).where(Employee.email == "admin@infosys-demo.com")):
            return
        demo_users = [
            Employee(
                employee_code="INFY-ADMIN-001",
                full_name="Aarav Sharma",
                email="admin@infosys-demo.com",
                department="Enterprise IT",
                designation="Platform Administrator",
                role=Role.ADMIN,
                hashed_password=hash_password("Admin@123"),
                leave_balance=30,
            ),
            Employee(
                employee_code="INFY-HR-001",
                full_name="Meera Nair",
                email="hr@infosys-demo.com",
                department="Human Resources",
                designation="HR Business Partner",
                role=Role.HR,
                hashed_password=hash_password("Hr@12345"),
                leave_balance=28,
            ),
            Employee(
                employee_code="INFY-EMP-001",
                full_name="Neel Prajapati",
                email="employee@infosys-demo.com",
                department="Digital Experience",
                designation="Systems Engineer Trainee",
                role=Role.EMPLOYEE,
                hashed_password=hash_password("Employee@123"),
                leave_balance=24,
            ),
        ]
        db.add_all(demo_users)
        db.flush()
        db.add_all(
            [
                Asset(asset_tag="INFY-MON-1001", category="Monitor", model="Dell 24-inch", status=AssetStatus.AVAILABLE),
                Asset(asset_tag="INFY-MSE-1001", category="Mouse", model="Logitech Wireless", status=AssetStatus.AVAILABLE),
                Asset(asset_tag="INFY-LTP-1001", category="Laptop", model="ThinkPad Enterprise", status=AssetStatus.AVAILABLE),
            ]
        )
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(Employee).where(Employee.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token=create_access_token(user.id), role=user.role)


@app.get("/auth/me", response_model=EmployeeRead)
def read_current_user(current_user: Employee = Depends(get_current_user)) -> Employee:
    return current_user


@app.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _: Employee = Depends(require_roles(Role.ADMIN)),
) -> Employee:
    duplicate = db.scalar(
        select(Employee).where((Employee.email == payload.email) | (Employee.employee_code == payload.employee_code))
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee email or code already exists")
    employee = Employee(
        employee_code=payload.employee_code,
        full_name=payload.full_name,
        email=payload.email,
        department=payload.department,
        designation=payload.designation,
        role=payload.role,
        leave_balance=payload.leave_balance,
        hashed_password=hash_password(payload.password),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@app.get("/employees", response_model=list[EmployeeRead])
def list_employees(
    db: Session = Depends(get_db),
    _: Employee = Depends(require_roles(Role.ADMIN, Role.HR)),
) -> list[Employee]:
    return list(db.scalars(select(Employee).order_by(Employee.full_name)))


@app.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
) -> Employee:
    if current_user.role == Role.EMPLOYEE and current_user.id != employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can view only their profile")
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@app.post("/leave/requests", response_model=LeaveRequestRead, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
) -> LeaveRequest:
    requested_days = (payload.end_date - payload.start_date).days + 1
    if payload.start_date < date.today():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Leave cannot start in the past")
    if requested_days > current_user.leave_balance:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Insufficient leave balance")
    request = LeaveRequest(employee_id=current_user.id, **payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@app.get("/leave/requests", response_model=list[LeaveRequestRead])
def list_leave_requests(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
) -> list[LeaveRequest]:
    query = select(LeaveRequest).order_by(LeaveRequest.created_at.desc())
    if current_user.role == Role.EMPLOYEE:
        query = query.where(LeaveRequest.employee_id == current_user.id)
    return list(db.scalars(query))


@app.patch("/leave/requests/{request_id}/decision", response_model=LeaveRequestRead)
def decide_leave_request(
    request_id: int,
    payload: DecisionUpdate,
    db: Session = Depends(get_db),
    reviewer: Employee = Depends(require_roles(Role.HR, Role.ADMIN)),
) -> LeaveRequest:
    leave_request = db.get(LeaveRequest, request_id)
    if leave_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if leave_request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request already reviewed")
    leave_request.status = payload.status
    leave_request.reviewer_id = reviewer.id
    leave_request.reviewer_comment = payload.reviewer_comment
    if payload.status == RequestStatus.APPROVED:
        employee = db.get(Employee, leave_request.employee_id)
        if employee is not None:
            employee.leave_balance -= (leave_request.end_date - leave_request.start_date).days + 1
    db.commit()
    db.refresh(leave_request)
    return leave_request


@app.post("/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    _: Employee = Depends(require_roles(Role.ADMIN)),
) -> Asset:
    if db.scalar(select(Asset).where(Asset.asset_tag == payload.asset_tag)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset tag already exists")
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@app.get("/assets", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db), _: Employee = Depends(get_current_user)) -> list[Asset]:
    return list(db.scalars(select(Asset).order_by(Asset.category, Asset.asset_tag)))


@app.post("/assets/requests", response_model=AssetRequestRead, status_code=status.HTTP_201_CREATED)
def create_asset_request(
    payload: AssetRequestCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
) -> AssetRequest:
    asset = db.get(Asset, payload.asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if asset.status != AssetStatus.AVAILABLE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset is not available")
    request = AssetRequest(employee_id=current_user.id, **payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@app.get("/assets/requests", response_model=list[AssetRequestRead])
def list_asset_requests(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
) -> list[AssetRequest]:
    query = select(AssetRequest).order_by(AssetRequest.created_at.desc())
    if current_user.role == Role.EMPLOYEE:
        query = query.where(AssetRequest.employee_id == current_user.id)
    return list(db.scalars(query))


@app.patch("/assets/requests/{request_id}/decision", response_model=AssetRequestRead)
def decide_asset_request(
    request_id: int,
    payload: DecisionUpdate,
    db: Session = Depends(get_db),
    reviewer: Employee = Depends(require_roles(Role.ADMIN)),
) -> AssetRequest:
    asset_request = db.get(AssetRequest, request_id)
    if asset_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset request not found")
    if asset_request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request already reviewed")
    asset = db.get(Asset, asset_request.asset_id)
    if payload.status == RequestStatus.APPROVED:
        if asset is None or asset.status != AssetStatus.AVAILABLE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset is no longer available")
        asset.status = AssetStatus.ALLOCATED
        asset.assigned_to_id = asset_request.employee_id
    asset_request.status = payload.status
    asset_request.reviewer_id = reviewer.id
    asset_request.reviewer_comment = payload.reviewer_comment
    db.commit()
    db.refresh(asset_request)
    return asset_request

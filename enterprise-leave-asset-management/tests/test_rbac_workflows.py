import os
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./test_enterprise_portal.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import TOKEN_STORE  # noqa: E402


def setup_function():
    TOKEN_STORE.clear()
    engine.dispose()
    if os.path.exists("test_enterprise_portal.db"):
        os.remove("test_enterprise_portal.db")
    Base.metadata.drop_all(bind=engine)


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_employee_leave_request_requires_hr_or_admin_decision_role():
    with TestClient(app) as client:
        employee_headers = login(client, "employee@infosys-demo.com", "Employee@123")
        start = date.today() + timedelta(days=5)
        leave_response = client.post(
            "/leave/requests",
            headers=employee_headers,
            json={
                "start_date": start.isoformat(),
                "end_date": (start + timedelta(days=1)).isoformat(),
                "leave_type": "Casual Leave",
                "reason": "Family function travel",
            },
        )
        assert leave_response.status_code == 201

        employee_decision = client.patch(
            f"/leave/requests/{leave_response.json()['id']}/decision",
            headers=employee_headers,
            json={"status": "approved", "reviewer_comment": "Self approval should fail"},
        )
        assert employee_decision.status_code == 403

        hr_headers = login(client, "hr@infosys-demo.com", "Hr@12345")
        hr_decision = client.patch(
            f"/leave/requests/{leave_response.json()['id']}/decision",
            headers=hr_headers,
            json={"status": "approved", "reviewer_comment": "Approved for planned leave"},
        )
        assert hr_decision.status_code == 200
        assert hr_decision.json()["status"] == "approved"


def test_admin_asset_approval_allocates_available_asset():
    with TestClient(app) as client:
        employee_headers = login(client, "employee@infosys-demo.com", "Employee@123")
        asset_request = client.post(
            "/assets/requests",
            headers=employee_headers,
            json={"asset_id": 1, "business_justification": "Need monitor for project delivery dashboard"},
        )
        assert asset_request.status_code == 201

        hr_headers = login(client, "hr@infosys-demo.com", "Hr@12345")
        hr_decision = client.patch(
            f"/assets/requests/{asset_request.json()['id']}/decision",
            headers=hr_headers,
            json={"status": "approved", "reviewer_comment": "HR cannot allocate assets"},
        )
        assert hr_decision.status_code == 403

        admin_headers = login(client, "admin@infosys-demo.com", "Admin@123")
        admin_decision = client.patch(
            f"/assets/requests/{asset_request.json()['id']}/decision",
            headers=admin_headers,
            json={"status": "approved", "reviewer_comment": "Allocated for delivery productivity"},
        )
        assert admin_decision.status_code == 200
        assert admin_decision.json()["status"] == "approved"

        assets = client.get("/assets", headers=employee_headers)
        assert assets.status_code == 200
        allocated_asset = next(asset for asset in assets.json() if asset["id"] == 1)
        assert allocated_asset["status"] == "allocated"

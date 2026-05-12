# Enterprise Leave & Asset Management System

An Infosys-inspired enterprise portal for managing employee leave and IT hardware allocation through secure role-based workflows.

## Why this project fits Infosys-style enterprise engineering

Infosys builds and maintains large internal and client-facing business platforms. This project demonstrates the same core capabilities at portfolio scale:

- **Role-based access control (RBAC):** Admin, HR, and Employee permissions are enforced at the API layer.
- **Relational data modelling:** Employees, leave requests, asset inventory, and allocation requests are linked with normalized SQLAlchemy models.
- **Workflow approvals:** HR can approve or reject leave, while Admin can approve or reject hardware requests.
- **Audit-friendly statuses:** Every request has status, timestamps, approver fields, and business comments.
- **Scalable API design:** FastAPI routers separate auth, employee, leave, and asset domains.
- **Database portability:** Uses SQLite locally, while the same ORM models can target PostgreSQL or MySQL through `DATABASE_URL`.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Database:** SQLite for local demos; PostgreSQL/MySQL-ready via SQLAlchemy
- **Security:** Password hashing, bearer-token authentication, RBAC dependencies
- **Testing:** Pytest with isolated in-memory database
- **Frontend:** React + Vite role-aware portal shell

## Roles

| Role | Capabilities |
| --- | --- |
| Admin | Register users, view employees, manage IT asset inventory, approve/reject asset requests |
| HR | View employees, approve/reject leave requests |
| Employee | View profile, apply for leave, track leave status, request IT assets |

## Quick start

```bash
cd enterprise-leave-asset-management
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the React frontend in a second terminal:

```bash
cd enterprise-leave-asset-management/frontend
npm install
npm run dev
```

Open the API documentation at `http://127.0.0.1:8000/docs`.

## Seeded demo users

The app creates demo users on first startup so reviewers can immediately test RBAC flows.

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@infosys-demo.com | Admin@123 |
| HR | hr@infosys-demo.com | Hr@12345 |
| Employee | employee@infosys-demo.com | Employee@123 |

## Example workflow

1. Login as `employee@infosys-demo.com` and copy the returned bearer token.
2. Create a leave request with `/leave/requests`.
3. Login as `hr@infosys-demo.com` and approve the leave request with `/leave/requests/{id}/decision`.
4. Login as employee and request an asset using `/assets/requests`.
5. Login as admin and approve the hardware request with `/assets/requests/{id}/decision`.

## API overview

| Domain | Endpoint examples |
| --- | --- |
| Auth | `POST /auth/login`, `GET /auth/me` |
| Employees | `POST /employees`, `GET /employees`, `GET /employees/{id}` |
| Leave | `POST /leave/requests`, `GET /leave/requests`, `PATCH /leave/requests/{id}/decision` |
| Assets | `POST /assets`, `GET /assets`, `POST /assets/requests`, `PATCH /assets/requests/{id}/decision` |

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./enterprise_portal.db` | SQLAlchemy database URL |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Bearer token validity window |
| `APP_NAME` | `Infosys Enterprise Leave & Asset Portal` | API display name |

## Test

```bash
pytest
```

## Included React frontend

The `frontend/` folder includes a Vite + React shell with demo login, backend token exchange, profile loading, and role-aware workspace actions. Expand it with these screens:

- Login and role-aware navigation shell
- Employee dashboard with leave and asset status cards
- Leave request form with balance preview
- HR approval queue with comments
- Asset catalog and request form
- Admin asset inventory and allocation queue

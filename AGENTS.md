# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

`safety-bms` is a safety production business management system (安全生产业务管理系统) with a FastAPI backend and a React + TypeScript frontend.

## Development Commands

### Backend

Run from `safety-bms/backend/`:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server (debug mode)
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "message"
alembic upgrade head

# Initialize default roles and admin user
PYTHONPATH=. python app/db/init_db.py

# Run API validation tests
PYTHONPATH=. python scripts/api_validation_tests.py
```

Backend config is loaded from `backend/.env` via Pydantic settings (`app/config.py`). Required vars include `SECRET_KEY`, `DB_*`, `REDIS_*`, and `MINIO_*`.

### Frontend

Run from `safety-bms/frontend/`:

```bash
# Install dependencies
npm install

# Dev server (port 5173, proxies /api to localhost:8000)
npm run dev

# Production build
npm run build

# Lint
npm run lint
```

## Architecture

### Backend (FastAPI)

- **Entry point**: `app/main.py` creates the FastAPI app, registers CORS, exception handlers, and routes under `/api/v1`.
- **Config**: `app/config.py` uses `pydantic-settings` (`BaseSettings`). `DEBUG=true` in `.env` makes auth cookies non-secure for local HTTP development.
- **Models**: `app/models/` uses SQLAlchemy 2.0 ORM. All models inherit from `Base` and commonly use `TimestampMixin` and `SoftDeleteMixin` (`app/db/base.py`).
- **CRUD pattern**: `app/crud/base.py` defines a generic `CRUDBase`. Domain CRUDs extend it (e.g., `app/crud/contract.py`).
- **API endpoints**: `app/api/v1/endpoints/` contains route modules for auth, users, customers, contracts, services, invoices, payments, and dashboard.
- **Services**: `app/services/` holds business logic such as `auth_service.py`, `invoice_service.py`, `payment_service.py`, `contract_amount_service.py` (unified amount calculations), and `minio_service.py`.
- **Auth & RBAC**:
  - Tokens are JWTs delivered via `httpOnly` cookies (`access_token`) with a fallback to the `Authorization` header.
  - `app/dependencies.py` provides `get_current_user` and `require_roles('admin', ...)` for endpoint guards.
  - Token blacklist is stored in Redis (SHA-256 hashed keys).
- **Critical business logic**:
  - Contract state machine: allowed transitions are enforced in `contracts.py`.
  - Invoice/payment amount limits: enforced with `with_for_update()` row locking in `invoice_service.py`, `payment_service.py`, and `payments.py` (update endpoint) to prevent race conditions.
  - Unified analytics filters: `app/utils/analytics_helpers.py` defines `filter_signed_contracts()`, `filter_valid_invoices()`, and `filter_valid_payments()` to ensure consistent statistical口径 across dashboard and analytics modules.
  - Rate limiting on `/login` and `/refresh` is backed by Redis.
- **File storage**: MinIO is used for contract attachments and service reports. Uploads are validated for extension (`pdf`, `doc`, `docx`, `jpg`, `jpeg`, `png`) and max size (`10MB`).

### Frontend (React + TypeScript + Vite)

- **Entry point**: `src/main.tsx` renders `src/App.tsx` inside a Redux `Provider`.
- **Routing**: `react-router-dom` v7 in `BrowserRouter`. Routes are defined in `App.tsx` with `PrivateRoute` guards and role-based access (`/users/*` requires `admin`).
- **State management**:
  - Redux Toolkit store in `src/store/index.ts`.
  - RTK Query base API in `src/store/api/baseApi.ts` with domain-specific API slices (`usersApi.ts`, `contractsApi.ts`, etc.).
  - Auth and UI state slices in `src/store/slices/`.
- **Pages**: `src/pages/` contains top-level views (Dashboard, Customers, Contracts, Services, Invoices, Payments, Users, Login). Each is typically a re-export to a folder module (e.g., `src/pages/Contracts.tsx` → `./Contracts/index`).
- **Shared types**: `src/types/index.ts` defines domain interfaces for contracts, invoices, payments, service orders, customers, and users.
- **Styling**: Ant Design 5 with Chinese locale (`zhCN`) and `dayjs` locale (`zh-cn`).
- **Proxy**: Vite dev server proxies `/api` to `http://localhost:8000` (see `vite.config.ts`).

## Important Patterns

- **Soft deletes**: `Contract`, `Invoice`, and `Payment` models all use `is_deleted` / `deleted_at` via `SoftDeleteMixin`. `CRUDBase.remove()` performs soft deletes automatically when the model has these fields. Queries should filter `is_deleted == False` unless intentionally fetching deleted records.
- **Cookie auth in local dev**: If `DEBUG=true`, the backend sets `secure=False` and `samesite="lax"` so cookies work over HTTP. In production, `DEBUG` should be `false` for secure cookies.
- **Database migrations**: Use Alembic from the `backend/` directory. After model changes, generate a migration and run `alembic upgrade head` before testing.
- **API validation tests**: The script at `backend/scripts/api_validation_tests.py` exercises core security and business logic fixes (auth cookies, admin self-lockout, weak passwords, contract state machine, invoice/payment race conditions, MinIO validation).

## Production Deployment Notes

- **Backend server**: Production uses `gunicorn` with `uvicorn.workers.UvicornWorker` (see `backend/Dockerfile` and `backend/gunicorn.conf.py`). Do not run `uvicorn` directly in production.
- **Swagger/Redoc**: Automatically hidden when `DEBUG=false` in `app/main.py`.
- **CORS**: `ALLOWED_ORIGINS` defaults to an empty list in production. You must explicitly set it in `.env`.
- **Database init**: `docker-compose.yml` includes a `backend-init` service that runs `alembic upgrade head` and `init_db.py` before the backend starts. No manual migration step is needed on deploy.
- **Scheduler lock**: `app/core/scheduler.py` uses a Redis distributed lock (`safety_bms:scheduler_lock`) to prevent duplicate scheduled jobs when scaling backend horizontally.
- **Logging**: `app/core/logging_config.py` outputs JSON-structured logs when `DEBUG=false`. Plain text logs are used in debug mode.
- **Frontend runtime config**: `frontend/public/env.js` allows runtime override of `API_BASE_URL` via the `API_BASE_URL` environment variable (replaced by `docker-entrypoint.sh`).

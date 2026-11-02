# Expense Receipt Processor — Backend

FastAPI + SQLAlchemy 2.0 + Alembic backend for the Expense Receipt Processor POC. See the
project root `CLAUDE.md` for full architecture, layering, and coding-standards context —
this file only covers how to set up and run the backend itself.

## Setup

```bash
cd backend
pip install -e ".[dev]"
cp .env.example .env   # then edit values as needed (JWT secret, Anthropic key, etc.)
```

## Database

```bash
alembic upgrade head        # apply migrations, creates ./data/app.db
python scripts/seed.py      # idempotent: 1 admin, 2 employees, 7 default categories
```

Run both from `backend/` — the SQLite path in `.env`/`Settings` (`./data/app.db`) and
Alembic's config are both relative to this directory.

**Seed credentials** (dev-only, not a real secret):
- Admin: `admin@example.com`
- Employees: `employee1@example.com`, `employee2@example.com`
- Password for all seeded users: `ChangeMe123!`

## Run

```bash
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`. Login via `POST /api/v1/auth/login`
(OAuth2 password flow — use the `/docs` "Authorize" button, or `username`/`password`
form fields with a seeded email/password).

## Tests

```bash
pytest --cov=app --cov-report=term-missing
```

## Lint / format / type-check / security

```bash
ruff check .
black --check .
mypy --strict src
bandit -r src
pip-audit
```

`.pre-commit-config.yaml` wires ruff, black, mypy, and bandit into a pre-commit hook —
run `pre-commit install` once per clone to enable it.

## Layout

```
src/app/
  main.py            app factory, CORS, exception handlers, /api/v1 router mounting
  core/              settings, exceptions, logging, security (hashing/JWT)
  db/                SQLAlchemy engine/session + declarative base
  models/            SQLAlchemy ORM models (User, Category, Receipt, ReceiptLineItem)
  schemas/           Pydantic v2 request/response DTOs
  repositories/      persistence only, no business rules
  services/          business logic, orchestration
  dependencies/      FastAPI Depends providers (DB session, auth, service wiring)
  routers/           HTTP I/O only — routers/ -> services/ -> repositories/
```

Only the `auth` + `health` slice exists so far. Future feature work (receipts,
categories, summaries) should use the `fastapi-react-feature-scaffold` skill to generate
the same layering for each new domain.

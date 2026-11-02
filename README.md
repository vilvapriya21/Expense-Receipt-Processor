# Expense Receipt Processor

A full-stack application for uploading expense receipts, extracting their details,
suggesting categories, and submitting them for finance review.

## Features

- Upload JPG, PNG, and PDF receipts
- Extract merchant, date, subtotal, tax, total, currency, and line items
- Suggest expense categories
- Let employees review and correct extracted values
- Submit receipts for approval
- Let admins approve or reject receipts and manage categories
- View employee and finance expense summaries
- Role-based access for employees and administrators

## Technology

- **Backend:** FastAPI, SQLAlchemy, SQLite, Alembic, Pydantic
- **Frontend:** React, TypeScript, Vite, Material UI, TanStack Query
- **Testing:** pytest, Vitest, React Testing Library

## Setup

### Backend

```powershell
cd backend
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000` and its API documentation is available at
`http://127.0.0.1:8000/docs`.

### Frontend

Open another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Demo accounts

All seeded accounts use the password `ChangeMe123!`.

| Role | Email |
|---|---|
| Admin | `admin@example.com` |
| Employee | `employee1@example.com` |
| Employee | `employee2@example.com` |

## Tests

```powershell
cd backend
pytest

cd ..\frontend
npm run test
```

## Project structure

```text
backend/        FastAPI API, database models, migrations, and tests
frontend/       React application
.claude/        Project rules, skills, subagents, and hooks
docs/evidence/  Assignment integration and usage evidence
docs/reviews/   Standards and architecture reviews
tools/          Read-only Expense MCP server and verifier
```

For detailed architecture and development standards, see [CLAUDE.md](CLAUDE.md).
For assignment evidence, see [docs/evidence/README.md](docs/evidence/README.md).

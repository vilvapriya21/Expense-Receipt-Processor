# Expense Receipt Processor

## 1. Overview

A POC where employees upload receipt images/PDFs; the system extracts merchant, date,
tax, subtotal, total, and currency, then suggests an expense category. The employee
reviews/corrects and submits. Admin/finance reviews submitted receipts, manages
categories, and views summaries.

**Roles**
- `EMPLOYEE` — uploads receipts, reviews/corrects extracted data, submits for approval.
- `ADMIN` — reviews submitted receipts, approves/rejects, manages categories, views summaries.

**Receipt status lifecycle**

```
UPLOADED -> EXTRACTED -> SUBMITTED -> APPROVED | REJECTED
```

- `UPLOADED`: file stored, not yet processed.
- `EXTRACTED`: extraction pipeline ran; fields populated, awaiting employee review.
- `SUBMITTED`: employee confirmed/corrected fields; locked for admin review.
- `APPROVED` / `REJECTED`: terminal states set by an admin.

## 2. Architecture

### Backend (`/backend`, src-layout: `backend/src/app/...`, `backend/tests/...`)

Layered, one-way dependency flow:

```
routers/ -> services/ -> repositories/
```

- `routers/` — HTTP I/O only: request/response wiring, status codes, calls into `services/` via `Depends`. No business logic.
- `services/` — business logic and orchestration (status transitions, category suggestion, validation).
- `repositories/` — persistence only; SQLAlchemy queries, no business rules.
- `schemas/` — Pydantic v2 request/response/DTO models.
- `dependencies/` — FastAPI `Depends` providers (DB session, current user/role, services).
- `core/` — cross-cutting: `settings.py` (config), `exceptions.py` (domain + HTTP error mapping), `logging.py`.
- `extraction/` — receipt extraction as a strategy interface (`BaseExtractor`), with concrete extractor implementations swappable behind it.

### Frontend (`/frontend`, Vite + React + TS), feature-sliced

```
src/features/<domain>/{components,hooks,services,types}
src/pages/
src/routes/
src/components/   (shared/reusable, cross-feature)
src/utils/
src/constants/
```

Each domain (e.g. `receipts`, `categories`, `summaries`) owns its own components, hooks,
API services, and types. Shared/dumb UI lives in `src/components/`; routing composition
in `src/routes/` and `src/pages/`.

## 3. Commands

**Install**
```
cd backend && pip install -e ".[dev]"
cd frontend && npm install
```

**Run (dev)**
```
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

**Tests**
```
cd backend && pytest
cd frontend && npm run test        # vitest
```

**Lint / format / type-check — backend**
```
cd backend && ruff check .
cd backend && black --check .
cd backend && mypy --strict src
cd backend && bandit -r src
```

**Lint / format / type-check — frontend**
```
cd frontend && npm run lint        # eslint
cd frontend && npm run format      # prettier
cd frontend && npm run typecheck   # tsc --noEmit
```

**Database migrations**
```
cd backend && alembic revision --autogenerate -m "<message>"
cd backend && alembic upgrade head
```

## 4. Coding standards

We follow the installed Cognine plugins as the source of truth:
- `python-fastapi-coding-standards-best-practices`
- `react-coding-standards-best-practices`

Key rules (short form — full detail in the plugin skills, do not duplicate here):

**Backend**
- `snake_case` for modules/functions/vars, `PascalCase` for classes, `UPPER_SNAKE` for constants.
- Strict layering: routers call services, services call repositories; never skip a layer, never call repositories from routers.
- All cross-cutting concerns (DB session, auth/role, config) injected via `Depends` — no globals, no manual instantiation in routers.
- No business logic, no raw SQLAlchemy queries, in routers.
- Full type hints everywhere; `mypy --strict` must pass.
- New/changed extractors implement the `extraction/` strategy interface — never special-cased in services.

**Frontend**
- Component/hook files `PascalCase.tsx` / `useCamelCase.ts`; one component per file.
- Feature code stays inside its `features/<domain>/` slice; only genuinely shared UI goes in `src/components/`.
- Approved libraries only: React Router, Zustand, TanStack Query, Axios, MUI, React Hook Form + Zod, date-fns, Vitest + React Testing Library. No other routing/state/HTTP/UI/form/date/test libs without an explicit decision.
- Server state via TanStack Query; local/UI state via Zustand or component state — never mixed.
- Forms via React Hook Form + Zod schemas; no ad-hoc manual validation.

## 5. How we work with Claude Code

- **Rules** — `.claude/rules/` contains the active path-scoped project rules. Read every
  rule whose `paths` frontmatter matches the files being changed:
  - @.claude/rules/backend-python.md
  - @.claude/rules/api-design.md
  - @.claude/rules/frontend-react.md
  - @.claude/rules/security.md
  - @.claude/rules/testing.md
  - @.claude/rules/git-workflow.md
- **Skills** — `.claude/skills/fastapi-react-feature-scaffold/` is the reusable skill for
  scaffolding or auditing full-stack vertical slices. `.claude/skills/receipt-extraction/`
  is the project-specific extraction and categorization skill. Usage evidence is in
  `docs/evidence/`.
- **Subagents** — `.claude/agents/test-engineer.md` writes and runs tests without changing
  production code. `.claude/agents/standards-reviewer.md` performs a read-only standards
  review. Use them after feature or bug-fix work in that order.
- **Hooks** — `.claude/settings.json` wires project pre-hooks that guard writes and shell
  commands, post-hooks that format/lint and track tests, and a stop reminder. Evidence is
  recorded in `docs/evidence/hooks.md`.
- **MCP** — `.mcp.json` registers the read-only `expense-data` server. Its
  `get_expense_overview` tool reports live user/category/receipt counts from the local
  SQLite database. Implementation and verification live under `tools/`; demonstration
  evidence is in `docs/evidence/mcp-expense-data.md`.

## 6. Definition of Done

A change is done only when:
1. All backend and frontend tests pass (`pytest`, `vitest`).
2. Lint, format, and type checks are clean (`ruff`, `black`, `mypy --strict`, `bandit`,
   `eslint`, `prettier`, `tsc --noEmit`).
3. The `standards-reviewer` subagent has been run against the diff with no unresolved
   findings.
4. Relevant docs (`/docs`, this file, affected `.claude/rules/*`) are updated.

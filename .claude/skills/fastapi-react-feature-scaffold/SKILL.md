---
name: fastapi-react-feature-scaffold
description: Scaffold a new domain feature or audit an existing vertical slice across a layered FastAPI backend and feature-sliced React frontend. Use for new resources/entities and for conformance checks of an existing full-stack feature. Do not use for small edits confined to one layer.
---

# FastAPI + React Feature Scaffold

Generates or audits a full vertical slice following a `routers -> services -> repositories`
backend and a feature-sliced frontend. It is project-agnostic and has two modes.

## When to use

- User asks to add a new resource/entity/feature (e.g. "add an Invoice feature", "scaffold
  CRUD for Customer").
- User asks whether an existing full-stack feature follows the expected layered structure
  or is ready for submission/merge. Use **Conformance audit mode** below without generating
  files.
- Confirm the target backend layout matches `routers/ -> services/ -> repositories/` with
  `schemas/`, `dependencies/`, `core/` and the target frontend layout matches
  `src/features/<domain>/{components,hooks,services,types}` before generating — if the repo
  uses a different layout, adapt file placement, keep the layering intent.

## Conformance audit mode

Use this mode for an existing feature. It is read-only unless the user separately asks
for fixes.

1. Trace one feature from frontend page/component through its query hook and API service
   to the backend router, service, repository, schema, and model.
2. Confirm routers only handle HTTP concerns, services own business rules, repositories
   own database queries, and dependency providers construct the graph.
3. Confirm frontend HTTP calls stay in feature services and server state stays in TanStack
   Query hooks rather than component or Zustand state.
4. Locate tests for the service, router, and important UI behavior. Report missing layers
   or tests explicitly rather than inventing evidence.
5. Run the repository's existing checks when authorized. Record exact commands and results.
6. Write a concise audit report to the project's established review/evidence location.

Do not copy templates, create migrations, or add a new entity in conformance audit mode.

## Inputs to collect first

Ask (or infer from the request) before generating:
- **Entity name**, singular, e.g. `Invoice` → derive:
  - `{{Name}}` = `Invoice`, `{{name}}` = `invoice`, `{{name_plural}}` = `invoices`,
    `{{name_plural_kebab}}` = `invoices`, `{{table_name}}` = `invoices`.
- Any domain fields the user already specified (add them to the schema/model; otherwise
  leave the `TODO` placeholder for the user to fill).

## Generation order

Generate in this exact order — each step depends on the previous one:

1. **`backend/src/app/schemas/<name>.py`** — from `templates/backend/schema.py.tmpl`.
2. **SQLAlchemy model** `backend/src/app/models/<name>.py` — from `templates/backend/model.py.tmpl`.
3. **`backend/src/app/repositories/<name>_repository.py`** — from `templates/backend/repository.py.tmpl`.
4. **`backend/src/app/services/<name>_service.py`** — from `templates/backend/service.py.tmpl`.
5. **`backend/src/app/routers/<name>.py`** — from `templates/backend/router.py.tmpl`, plus a
   `dependencies/<name>.py` provider wiring `AsyncSession -> Repository -> Service`.
   Register the router in the app entrypoint (`app.include_router(...)`).
6. **Alembic migration**: run `alembic revision --autogenerate -m "add <name> table"` after
   the model exists, then review the generated migration by hand.
7. **Backend tests**: `backend/tests/.../test_<name>_service.py` and
   `test_<name>_router.py` from the matching templates.
8. **`frontend/src/features/<name_plural>/types/index.ts`** — from `templates/frontend/types.ts.tmpl`.
9. **`frontend/src/features/<name_plural>/services/<name>Service.ts`** — from
   `templates/frontend/service.ts.tmpl` (Axios, via the shared API client).
10. **`frontend/src/features/<name_plural>/hooks/use<Name>.ts`** — from
    `templates/frontend/useEntity.ts.tmpl` (TanStack Query: list/get/create/update).
11. **`frontend/src/features/<name_plural>/components/<Name>List.tsx`** — from
    `templates/frontend/EntityList.tsx.tmpl`.
12. **Frontend test**: `<Name>List.test.tsx` from `templates/frontend/EntityList.test.tsx.tmpl`.

## Placeholder reference

| Placeholder | Example (`Invoice`) |
|---|---|
| `{{Name}}` | `Invoice` |
| `{{name}}` | `invoice` |
| `{{name_plural}}` | `invoices` |
| `{{name_plural_kebab}}` | `invoices` |
| `{{table_name}}` | `invoices` |

Replace every placeholder in every copied template — do not leave `{{...}}` in generated
files. Fill in real domain fields where the templates have a `TODO` instead of leaving
generic/empty fields when the user has already specified what the entity contains.

## Rules while generating

- Never put business logic in the router or the repository — only in the service.
- Never make raw HTTP calls or import Axios outside `services/` on the frontend.
- Server state goes through TanStack Query hooks; never store list/detail data in Zustand.
- Match existing project conventions (import style, error classes, API client) over the
  template verbatim if they conflict — the templates are a starting shape, not a contract.

## Checklist (must verify before declaring done)

1. `ruff check .` and `black --check .` clean on the new backend files.
2. `mypy --strict` clean on the new backend files.
3. `alembic upgrade head` applies the new migration without error.
4. `pytest` passes, including the new service and router tests.
5. `eslint` and `tsc --noEmit` clean on the new frontend files.
6. `vitest` passes, including the new component test.
7. No leftover `{{...}}` placeholders anywhere in generated files.
8. The new router is registered and reachable (spot-check the OpenAPI schema or a manual
   request).

Report the checklist results explicitly; do not claim the feature is done if any item
fails — fix it first.

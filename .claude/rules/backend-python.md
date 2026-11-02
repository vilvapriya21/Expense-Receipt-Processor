---
paths: backend/**/*.py
---

# Backend Python Rules

- Name modules and functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Prefix booleans with `is_`, `has_`, `should_`, or `can_`.
- Keep files under ~500 lines; split when they grow past that.
- Routers orchestrate only (parse request, call a service, return response) — no business rules.
- Put business rules in `services/`; put all DB access in `repositories/`. Never query the DB from a router or service directly.
- Inject dependencies (DB session, current user, services, clients) via `Depends` — never instantiate external clients (HTTP, storage, LLM/OCR) inside business functions.
- Add full type hints to every function signature; code must pass `mypy --strict`.
- Write Google-style docstrings on every public function/class.
- Define request models as Pydantic v2 schemas with `model_config = ConfigDict(extra="forbid")`.
- Raise from a custom exception hierarchy defined in `core/exceptions.py`; map each exception to a consistent JSON error response — never leak raw exceptions or stack traces to the client.
- Log with structured logging (`core/logging.py`). Never log PII or full receipt text/content — log identifiers (receipt ID, user ID) only.

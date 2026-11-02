---
paths: backend/tests/**, frontend/src/**/*.test.tsx
---

# Testing Rules

- Name pytest tests `test_<feature>_<scenario>_<expected_result>`.
- Mirror the source tree structure under `backend/tests/`.
- Mock only external boundaries — LLM/OCR client, filesystem, clock — never mock internal services/repositories under test.
- Use an in-memory or temporary SQLite database per test; never share state across tests.
- Build test data with factories, not hand-rolled fixtures duplicated across files.
- Keep backend service-layer coverage at or above 80%.

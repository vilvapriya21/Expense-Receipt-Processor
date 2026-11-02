---
paths: backend/src/app/routers/**
---

# API Design Rules

- Name resources with plural nouns (`/receipts`, `/categories`), never verbs.
- Prefix every route with `/api/v1`.
- Use correct HTTP status codes: `200` read/update, `201` create, `204` delete with no body, `400` validation, `401`/`403` auth, `404` not found, `409` conflict, `422` schema errors.
- Paginate list endpoints with `page` and `size` query params; return total count alongside results.
- Return errors in a consistent envelope: `{"code": "...", "message": "...", "details": {...}}` — never a bare string or stack trace.
- Version breaking changes with a new `/api/v2` prefix rather than mutating `v1` contracts.

---
paths: backend/**, frontend/src/**
---

# Security Rules

- Validate every upload: restrict to allowed MIME types (`image/jpeg`, `image/png`, `application/pdf`), verify the file's magic bytes against the claimed type, and enforce a max size read from settings.
- Never trust the client-supplied filename; generate a randomized stored filename on save.
- Keep all secrets in environment variables / `.env` — never commit real secrets; keep `.env.example` current with every new variable.
- Enforce role checks via a dependency on every admin-only route.
- Employees may only access/modify their own receipts — enforce ownership checks in the service layer, not just the UI.

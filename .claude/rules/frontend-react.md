---
paths: frontend/src/**/*.{ts,tsx}
---

# Frontend React Rules

- Name components `PascalCase`, hooks `useCamelCase`, services/utils `camelCase`.
- Keep lines under 100 characters.
- Components render only — extract logic (state, effects, derived values) into hooks.
- Make HTTP calls only from `services/`, through the shared Axios client — never `fetch`/`axios` directly in components or hooks.
- Hold server state in TanStack Query only — never duplicate it into Zustand.
- Use Zustand only for auth/session state, not for server or server-derived data.
- Build forms with React Hook Form + a Zod schema — no ad-hoc manual validation.
- Never use `any`; type and document (JSDoc) every exported component's props.
- Write accessible markup: semantic HTML elements, a `<label>` for every input, full keyboard navigability.

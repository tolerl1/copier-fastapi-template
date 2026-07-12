# Python Backend Instructions

When working in this repository:

1. Use `uv run` for tests, linting, type checking, and migrations.
2. Add new business capabilities as named scopes backed by `ScopeSettings` and `ScopeRegistry`.
3. Inject services instead of constructing infrastructure directly in route handlers.
4. Preserve async-first implementations for FastAPI, SQLAlchemy, Redis, and the optional Azure queue adapter (`azure` extra; import it lazily, never at module scope).
5. Prefer queue dispatch for long-running workflows.
6. Refresh dependency-provided agent skills with `uv run library-skills --tool-skill install --claude --yes --all`.

# copier-fastapi-template

A [Copier](https://copier.readthedocs.io/) template for spinning up new FastAPI
microservices. It's a Jinja-templated mirror of
[tolerl1/fastapi-template](https://github.com/tolerl1/fastapi-template) — same
stack, same conventions, same hardening (real Postgres/Redis, SQL-level
pagination, a lightweight `engine.connect()` health check, per-domain
`APIRouter`s, `Annotated` dependency aliases, Alembic migrations, GitHub
Actions CI with real service containers) — but with all the project-specific
values (package name, pyproject metadata, Docker Compose credentials, CI env
vars, etc.) turned into generation-time prompts instead of a 30-place
find-and-replace.

This repository's only job is to be a Copier source. The actual project
scaffold lives under [`template/`](./template); everything else at the repo
root (`copier.yml`, this README, the template-verification CI workflow) is
metadata for authoring the template itself, not part of any generated
project.

## Usage

Install [Copier](https://copier.readthedocs.io/en/stable/#installation) (via
`uv`, `pipx`, or `pip`), then generate a new project:

```bash
uv tool install copier   # or: pipx install copier
copier copy gh:tolerl1/copier-fastapi-template path/to/new-project
```

Copier will prompt for:

| Prompt | What it controls |
| --- | --- |
| `package_name` | Python import name (snake_case, validated as a Python identifier). Becomes `src/<package_name>/`, `tests/<package_name>/`, the Postgres user/db name, and the `<PACKAGE_NAME>_` settings env var prefix. |
| `project_name` | Human-readable app name — the FastAPI title and README heading. Defaults to a title-cased version of `package_name`. |
| `description` | One-line description used in `pyproject.toml` and the README. |
| `author_name` | Used in `LICENSE`. |
| `python_version` | `3.12` or `3.13`. Drives `requires-python`, the Dockerfile base image, `ruff`'s `target-version`, and `pyright`'s environment. |
| `include_example_endpoint` | Off by default. Turn it on to keep the `/items` example (`ItemModel` → `SqlAlchemyItemRepository` → `ItemService` → route) that demonstrates the request/service/repository/DB pattern. Off means a clean project with no example domain code to delete by hand. |
| `enable_telemetry` | On by default. Wires up OpenTelemetry (tracer provider, OTLP/console exporter, FastAPI instrumentation, trace IDs in log lines) and the four `opentelemetry-*` dependencies. Off drops `core/telemetry.py` and those dependencies entirely for services that don't run a collector. |

`package_slug` (hyphenated form of `package_name`, used for the `pyproject.toml`
`name` and the `[project.scripts]` entry) and `env_prefix` are derived
automatically and aren't prompted.

To pre-answer prompts non-interactively (useful for scripting or CI):

```bash
copier copy gh:tolerl1/copier-fastapi-template path/to/new-project \
  --data package_name=orders_service \
  --data project_name="Orders Service" \
  --data description="Owns order lifecycle and fulfillment." \
  --data author_name="Your Name" \
  --data python_version=3.12 \
  --data include_example_endpoint=false \
  --data enable_telemetry=true
```

### After generating

```bash
cd path/to/new-project
cp .env.example .env
uv sync
docker compose up -d db redis
uv run alembic upgrade head
uv run <package_slug>
```

Then wire up git hooks — note the explicit `-t` flags, without them `prek
install` only wires up the `pre-commit` stage and the `commit-msg`/`pre-push`
hooks silently never install:

```bash
uv tool install prek
prek install -t pre-commit -t commit-msg -t pre-push
```

`azure-storage-queue` is an optional dependency (the `azure` extra) rather
than a hard install, since most projects only ever use the `memory` or
`redis` queue backend. Install it only if you set
`<PACKAGE_NAME>_QUEUE_BACKEND=azure_storage_queue`:

```bash
uv sync --extra azure
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
(enforced by the `commit-msg` hook and CI). `.github/workflows/release.yml`
in the generated project reads them on every push to `main` to bump the
version, update `CHANGELOG.md`, and push a tag via Commitizen.

### Updating a project after the template changes

Copier supports re-applying template updates to a project generated from an
earlier version:

```bash
cd path/to/existing-project
copier update --defaults
```

This works because `copier copy` records the answers you gave in
`.copier-answers.yml` at the project root — don't delete that file. Running
`copier update` interactively (no `--defaults`) is fine in a terminal, where
it can re-prompt you if needed; in a script or CI it fails with "Interactive
session required" unless you pass `--defaults` (reuse the recorded answers)
and/or `--data`/`--data-file` to supply any new questions non-interactively.

## Repository layout

```text
copier.yml                        # Prompts, validation, derived variables
README.md                         # This file
LICENSE                           # This template repo's own license
.github/dependabot.yml            # Keeps this repo's own GitHub Actions pinned versions current
.github/workflows/test-template.yml  # Renders the template (matrixed across
                                      # include_example_endpoint, enable_telemetry,
                                      # and python_version) and runs the
                                      # generated project's own ruff/pyright/pytest
template/                         # Everything below here is the actual
                                   # Copier payload (the "_subdirectory")
  copier.yml is NOT in here — Copier config always lives at the repo root.
  src/{{ package_name }}/...
  tests/{{ package_name }}/...
  pyproject.toml.jinja, Dockerfile.jinja, docker-compose.yml.jinja, ...
  Makefile.jinja, .editorconfig       # Task runner + editor defaults for the generated project
  CHANGELOG.md                        # Seed file; Commitizen appends to it on release
  .github/workflows/ci.yml.jinja      # The *generated project's* own CI
  .github/workflows/release.yml.jinja # Commitizen version bump + changelog on push to main
  .github/dependabot.yml              # uv / github-actions / docker update PRs for the generated project
  .github/CONTRIBUTING.md.jinja, CODE_OF_CONDUCT.md, PULL_REQUEST_TEMPLATE.md,
    ISSUE_TEMPLATE/                   # Community/process files for the generated project
  alembic/
```

A `template/` subdirectory (Copier's `_subdirectory` mechanism) is used
instead of a flat layout because this repo's own README and CI workflow are
genuinely different files from the generated project's README and CI
workflow — they can't share a source path without one clobbering the other
at render time. Everything under `template/` is the payload; everything
above it is about maintaining the template itself.

## Verifying changes to this template

`.github/workflows/test-template.yml` renders the template across a matrix of
`include_example_endpoint`, `enable_telemetry`, and `python_version` against
real Postgres and Redis service containers, then runs `ruff check`,
`ruff format --check`, `pyright`, and `pytest` inside each rendered project (a
session-scoped fixture in the rendered project's own `tests/conftest.py`
applies Alembic migrations to the test database automatically — no separate
migration step is needed). Run the same steps locally before pushing template
changes:

```bash
uv tool install copier
copier copy . /tmp/rendered-with-items \
  --data package_name=my_service --data include_example_endpoint=true \
  --data enable_telemetry=true \
  --defaults --trust --vcs-ref HEAD
cd /tmp/rendered-with-items
uv sync
uv run ruff check . && uv run ruff format --check . && uv run pyright
docker compose up -d db redis   # or point *_TEST_DATABASE_URL / *_TEST_REDIS_URL elsewhere
uv run pytest
```

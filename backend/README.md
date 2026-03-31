# Investment System — Backend

FastAPI backend for the Investment System. Python 3.12+, managed with [uv](https://docs.astral.sh/uv/).

---

## Table of contents

- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the app](#running-the-app)
- [Dependency management (uv)](#dependency-management-uv)
- [Formatting and linting (Ruff)](#formatting-and-linting-ruff)
- [Tests (pytest)](#tests-pytest)
- [Running from the monorepo root](#running-from-the-monorepo-root)
- [App settings](#app-settings)
- [Alembic (migrations)](#alembic-migrations)
- [Recommendations](#recommendations)

---

## Project structure

```
backend/
├── main.py                        # FastAPI app entry point
├── pyproject.toml                 # Project metadata and dependencies
├── ruff.toml                      # Ruff formatter and linter config
├── alembic/                       # DB migration environment (alembic)
├── config/                        # App configuration and settings
├── database/                      # DB engine/session helpers
├── routes/                        # Route handlers (one file per domain)
├── src/                           # Business logic and domain code
│   ├── models/                    # DB models (ORM / Pydantic models)
│   ├── repositories/              # Data access layer / repositories
│   └── services/                  # Business services (use repositories)
└── tests/                         # Pytest test suite
```

This repo is a monorepo — a `frontend/` (Next.js) directory will sit alongside `backend/`. All commands below assume you are working within the `backend/` directory

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — install once globally:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## Setup

```bash
cd backend
uv sync            # creates .venv and installs all dependencies (including dev)
# initialise DB schema after dependencies are installed
uv run alembic upgrade head
```

---

## Running the app

```bash
cd backend
uv run fastapi dev              # development server with auto-reload — http://localhost:8000
```

To run the database 

```bash
# from the repository root 
docker-compose up 
```

API docs are available at:
- Swagger UI: http://localhost:8000/docs

---

## Dependency management (uv)

All dependency commands must be run from the `backend/` directory.

```bash
uv add httpx                    # add a runtime dependency
uv add --dev pytest-cov         # add a dev-only dependency
uv remove httpx                 # remove a dependency
uv sync                         # install/update all deps to match pyproject.toml + uv.lock
uv lock                         # regenerate uv.lock without installing
```

> Commit both `pyproject.toml` and `uv.lock` to git. `uv.lock` ensures every team member and CI environment installs identical versions.

---

## Formatting and linting (Ruff)

[Ruff](https://docs.astral.sh/ruff/) handles both formatting (replaces Black) and linting (replaces flake8/isort/pylint) in one tool. Config lives in `ruff.toml`.

```bash
# from backend/
uv run ruff format .                # format all files
uv run ruff format main.py          # format a specific file
uv run ruff check .                 # lint — report issues on all files
uv run ruff check main.py           # lint a specific file
uv run ruff check . --fix           # lint — auto-fix fixable issues on all files
```

### On save (automatic)

Formatting and lint fixes are applied automatically on every file save if your editor is configured below. No manual commands needed.

#### VS Code

1. Install the [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) (`charliermarsh.ruff`)
2. Done — settings are already committed in `.vscode/settings.json`

#### IntelliJ / PyCharm

1. Not set up, add the extension and create the idea settings

> The extension/plugin is required for on-save behaviour. Without it, you need to run the commands above manually.

---

## Tests (pytest)

```bash
cd backend
uv run pytest                        # run all tests
uv run pytest -v                     # verbose output
uv run pytest tests/test_system.py   # run a specific file
uv run pytest -k "test_health"       # run tests matching a name pattern
```

Tests live in `tests/`. Test files must be named `test_*.py` and test functions must be prefixed `test_`.

---


### App settings (pydantic-settings)

We use `pydantic-settings` to centralise configuration. Define a `Settings` class in `config/settings.py` and expose a module-level `settings` instance so application code can import configuration with:

```python
from config.settings import settings

# example usage
settings.database.postgres_user
```

`pydantic-settings` will load values from environment variables, `.env` files, or other configured sources — see the library docs for advanced patterns.


---

### Alembic (migrations)

- Create a new migration (autogenerate):

```bash
cd backend
uv run alembic revision -m "create account table"
```

- Apply migrations:

```bash
uv run alembic upgrade head
```

- Revert the most recent migration:

```bash
uv run alembic downgrade -1
```

---

## Recommendations

- **`uv.lock` in git** — always commit the lockfile. This guarantees reproducible installs across machines and CI.
- **Never commit `.venv/`** — it's in `.gitignore` and is local to each machine. Run `uv sync` to recreate it.
- **Type hints everywhere** — the linter enforces this (`ANN` rules). FastAPI uses type hints at runtime for request validation and OpenAPI schema generation, so they are functional, not just documentation.
- **Pydantic models for route responses** — prefer `BaseModel` return types. Gives you validation, serialisation, and auto-generated OpenAPI schemas.
- **One router per domain** — keep routes split by feature (e.g. `routes/system.py`, `routes/items.py`) and include them in `main.py`. Avoid putting route handlers directly in `main.py`.
  - **__init__.py files** — Include `__init__.py` in package directories so Python recognises them as packages; this keeps imports predictable in development and test environments.

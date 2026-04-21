# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a FastAPI backend for the ZIM Farm distributed system. The architecture consists of:

### Core Components

**API Layer** (`src/zimfarm_backend/api/routes/`)
- REST API at `/v2` prefix with resource-based routing
- Auth, schedules, tasks, workers, users, languages, platforms, offliners, contexts, tags, blobs endpoints
- Pydantic models for request/response validation
- Custom exceptions: `RecordAlreadyExistsError`, `RecordDoesNotExistError`

**Database Layer** (`src/zimfarm_backend/db/`)
- SQLAlchemy ORM with PostgreSQL (via psycopg)
- Custom `Session` factory with BSON serialization for mixed data types
- Session management via `gen_dbsession()` (auto-commit/rollback) and `gen_manual_dbsession()`
- Alembic migrations in `src/zimfarm_backend/migrations/versions/`

**Background Tasks** (`src/zimfarm_backend/background_tasks/`)
- Periodic task scheduler (cancel incomplete/stale tasks, history cleanup, CMS notifications, orphaned blob deletion)
- Configurable intervals defined in `entrypoint.py`
- Runs as separate service via `background-tasks` CLI command

### Common Patterns

1. **Database Sessions**: Use `gen_dbsession()` for automatic transaction management, `gen_manual_dbsession()` for manual control
2. **Validation**: Pydantic models in route-specific `models.py` files
3. **Business Logic**: Located in route-specific `logic.py` files
4. **Testing**: pytest with fixtures in `tests/conftest.py` and `tests/routes/conftest.py`

## Development Commands

```bash
# Setup (from project root)
cd backend
hatch shell                    # Activate virtual environment

# Running
uvicorn zimfarm_backend.main:app --reload --port 8000  # Start dev server
python -m zimfarm_backend.background_tasks.entrypoint   # Start background tasks

# Testing
python -m pytest               # Run all tests
python -m pytest tests/routes/test_user.py -k test_list_users_no_auth  # Run specific test
python -m pytest tests/ -m num_users  # Run tests with custom markers
inv coverage --args "-vvv"

# Linting & Formatting
inv lintall                    # Check linting (black, ruff)
inv fixall                     # Auto-fix formatting issues
inv checkall                   # Static type checking (pyright)
```

## API Structure

| Route | Resource |
|-------|----------|
| `/v2/auth/*` | Authentication (JWT tokens, refresh tokens) |
| `/v2/schedules` | Recipe management (create, list, clone, history) |
| `/v2/requested-tasks` | Pending task requests |
| `/v2/tasks` | Active/completed tasks with events |
| `/v2/workers` | Worker registration and status |
| `/v2/users` | User management |
| `/v2/platforms` | Available scraping platforms |
| `/v2/offliners` | Scraper configurations |
| `/v2/languages` | Supported languages |
| `/v2/contexts` | Context definitions |
| `/v2/tags` | Tag management |
| `/v2/blobs` | Arbitrary data storage |

## Key Configuration

- **Python**: 3.13 only
- **Database**: PostgreSQL (required: `POSTGRES_URI` env var)
- **Dependencies**: Hatch for managing (see `pyproject.toml`)
- **Migrations**: Alembic, auto-upgrade on start if `ALEMBIC_UPGRADE_HEAD_ON_START=true`
- **Backend services**: ZIM upload, logs upload, CMS notifications (configurable via env vars)

## Authentication

The backend supports multiple authentication modes configured via `AUTH_MODES`:

| Mode | Description |
|------|-------------|
| `local` | Internal Zimfarm JWT tokens (HS256) |
| `oidc` | OIDC Authorization Code flow with PKCE (RAuthy, Ory Kratos) |
| `rauthy` | RAuthy OIDC tokens (self-hosted) |

**Key environment variables:**
- `AUTH_MODES`: Comma-separated auth modes (default: "local")
- `JWT_SECRET`: Secret for local token signing
- `OAUTH_BASE_URL`: OAuth provider base URL
- `OAUTH_JWKS_URI`: JWKS endpoint for external providers (default: Kiwix Ory)
- `OAUTH_ISSUER`: Token issuer for validation (default: Kiwix issuer)
- `OAUTH_OIDC_CLIENT_ID`: Client ID for audience validation
- `OAUTH_AUDIENCE`: Audience for RAuthy validation (optional)
- `OAUTH_OIDC_LOGIN_REQUIRE_2FA`: Require 2FA authentication (default: true)

**Token validation:** See `src/zimfarm_backend/api/token.py` for decoder chain implementation.

**Note:** Session-based authentication (`oauth-session` mode) has been removed in favor of OIDC Authorization Code flow with PKCE.

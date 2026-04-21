# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### File Organization

- NEVER save to root folder use the directories below                                    
- Use `/.claude` for Claude Code configuration for AI assistant settings and workflow customization
- Use `/.claude-flow` for Claude Flow V3 configuration for multi-agent swarm orchestration and memory management
- Use `/.github` for GitHub Actions workflows and issue templates for CI/CD and repository management
- Do not touch `.vscode`
- Use `/backend` for Python FastAPI backend server containing API routes, authentication, database models, and worker management
- Use `./dev` for Development environment setup including docker-compose configuration for local development stack
- Use `/dnscache` for Dnsmasq DNS caching container to cache DNS requests for scrapers with consistent resolution
- Use `/frontend-ui` for Vue.js frontend application for user interface to manage recipes, tasks, and workers
- Use `/healthcheck` for Health monitoring service that checks Zimfarm services status and displays results as HTML
- Use `/monitor` for Netdata monitoring infrastructure with parent (central server) and child (worker agents) components
- Use `/receiver` for Authenticated SSH server (chrooted) to receive ZIM files and logs from workers via SCP/SFTP
- Use `/recipesauto` for Automated recipe management tool for creating and maintaining groups of ZIM recipes (StackExchange, TED)
- Use `/relay` for Simple relay service (likely for healthcheck or API proxy functionality)
- Use `/uploader` for Dedicated service for uploading ZIM files and logs to warehouses via SFTP/SCP
- Use `/watcher` for StackExchange dump watcher that monitors for updates and schedules ZIM creation tasks
- Use `/worker` for Worker manager and task worker code with documentation for running ZIM creation tasks on distributed workers
- Use `/workers` for Legacy directory containing backwards compatibility symlink (zimfarm.sh script)

## Architecture Overview

ZIM Farm is a distributed system for building ZIM files (compressed web content archives). The architecture consists of:

### Backend (Python/FastAPI)
- REST API at `/v2` prefix with PostgreSQL database
- Core entities: schedules (recipes), tasks, workers, users, offliners
- Background tasks for async operations (task cleanup, CMS notifications, etc.)
- Uses Pydantic for data validation, Alembic for migrations
- Test framework: pytest

### Frontend (Vue 3 + Vuetify)
- Single-page application with Vue Router
- State management with Pinia
- Makes API calls to backend at `/v2`
- Uses Highlight.js for code display

### Worker System (Python)
- Two-tier: manager (spawns tasks) + task-worker (executes scrapers)
- Communicates with backend API for task assignment
- Uses Docker to run scraper containers

### Supporting Services
- **receiver**: SSH server for receiving ZIM files and logs
- **dnscache**: DNS caching via dnsmasq
- **uploader**: Handles file uploads via SFTP

## Common Commands

### Backend
```bash
cd backend
hatch shell                    # Activate virtual environment
uvicorn zimfarm_backend.main:app --reload --port 8000  # Start dev server
python -m pytest               # Run all tests
python -m pytest tests/routes/test_user.py -k test_list_users_no_auth  # Run specific test
```

### Frontend
```bash
cd frontend-ui
yarn install                   # Install dependencies
yarn dev                       # Start dev server (Vite, port 5173)
yarn build                     # Production build
yarn lint                      # ESLint with auto-fix
yarn format                    # Prettier formatting
```

### Development Stack (Docker)
```bash
cd dev
docker compose -p zimfarm up -d   # Start all services
docker restart zf_backend         # Restart backend
```

## API Structure

The backend API routes are organized by resource:
- `/v2/auth/*` - Authentication (JWT tokens)
- `/v2/schedules` - Recipe management (create, list, clone)
- `/v2/requested-tasks` - Pending task requests
- `/v2/tasks` - Active/completed tasks
- `/v2/workers` - Worker registration and status
- `/v2/users` - User management
- `/v2/platforms` - Available scraping platforms
- `/v2/offliners` - Scraper configurations
- `/v2/languages` - Supported languages
- `/v2/blobs` - Arbitrary data storage (JSON blobs)

## Key Patterns

1. **Database**: SQLAlchemy ORM with explicit session management
2. **Validation**: Pydantic models for all API request/response schemas
3. **Error handling**: Custom exceptions (RecordAlreadyExistsError, RecordDoesNotExistError)
4. **Testing**: pytest with conftest.py providing fixtures and test database
5. **Frontend state**: Pinia stores with config plugin for runtime configuration

## Authentication

ZIM Farm supports multiple authentication modes configured via the `AUTH_MODES` environment variable:

### Local Auth (`local`)
- Username/password authentication using Zimfarm's internal database
- JWT tokens signed with HS256 using `JWT_SECRET`

### OIDC Authorization Code Flow with PKCE (`oidc`, `rauthy`)
- External identity provider authentication (e.g., RAuthy, Ory Kratos)
- Uses OIDC Authorization Code flow with PKCE for public clients
- Tokens validated using JWKS from the configured provider
- **RAuthy**: Self-hosted Rust-based OIDC provider
- **OIDC**: Generic OIDC provider (Kiwix Ory compatible)

### Deprecated: Session-based Auth (`oauth-session`)
- Session-based auth has been removed in favor of OIDC Authorization Code flow

Configuration environment variables:
- `AUTH_MODES`: Comma-separated list of auth modes (default: "local")
- `OAUTH_BASE_URL`: Base URL for OAuth/OIDC provider
- `OAUTH_CLIENT_ID`: OAuth client identifier
- `OAUTH_ISSUER`: Token issuer for validation
- `OAUTH_JWKS_URI`: JWKS endpoint for token validation
- `OAUTH_OIDC_CLIENT_ID`: Client ID for OIDC audience validation
- `OAUTH_AUDIENCE`: Audience for RAuthy validation (optional)
- `OAUTH_OIDC_LOGIN_REQUIRE_2FA`: Require 2FA authentication (default: true)

## Setup Requirements

- **Backend**: Python 3.13, PostgreSQL, Hatch
- **Frontend**: Node.js 24, Yarn classic
- **Workers**: Docker, Python 3.13
- **Dev stack**: Docker Compose

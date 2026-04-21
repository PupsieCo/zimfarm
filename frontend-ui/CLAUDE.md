# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this frontend-ui repository.

## Project Overview

ZIM Farm Frontend UI is a Vue 3 application that provides a user interface for managing ZIM file creation tasks. It connects to a FastAPI backend at `/v2` API endpoints.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **UI Library**: Vuetify 3 (Material Design components)
- **Routing**: Vue Router 4
- **State Management**: Pinia
- **HTTP Client**: Axios
- **Build Tool**: Vite 7
- **TypeScript**: Strict mode with vue-tsc
- **Testing**: Vitest with Playwright for E2E
- **Code Quality**: ESLint 9, Prettier 3

## Directory Structure

```
frontend-ui/
├── src/
│   ├── api/                 # API service layer (Axios instances)
│   ├── assets/              # Static assets (CSS, images)
│   ├── components/          # Vue components (reusable)
│   ├── config.ts            # Runtime configuration service
│   ├── constants.ts         # App-wide constants (roles, categories, etc.)
│   ├── main.ts              # App entry point
│   ├── router/              # Vue Router configuration
│   ├── services/            # Service layer (auth, HTTP clients)
│   ├── stores/              # Pinia state management
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   └── views/               # Page-level components
├── public/                  # Public static files
├── .claude/                 # Claude AI configuration
├── index.html               # HTML entry point
├── nginx-default.conf     # Nginx configuration for deployment
├── vite.config.ts           # Vite build configuration
├── vitest.config.ts         # Vitest test configuration
└── tsconfig*.json           # TypeScript configuration files
```

## Common Commands

```bash
yarn install        # Install dependencies
yarn dev            # Start dev server (Vite, port 5173)
yarn build          # Production build
yarn lint           # ESLint with auto-fix
yarn format         # Prettier formatting
yarn format-check   # Check formatting without modifying files
yarn type-check     # Run Vue TypeScript compiler
```

## Configuration

### Runtime Configuration

The app loads configuration from `/config.json` at runtime via `ConfigService`:

```typescript
import { ConfigService } from '@/config'

const config = await ConfigService.getConfig()
// config.ZIMFARM_WEBAPI
// config.MATOMO_ENABLED
// config.OAUTH_CLIENT_ID
// etc.
```

**Config keys:**
- `ZIMFARM_WEBAPI`: Backend API URL
- `ZIMFARM_ZIM_DOWNLOAD_URL`: Base URL for ZIM file downloads
- `MATOMO_ENABLED`: Analytics tracking toggle
- `MATOMO_HOST`: Matomo server URL
- `MATOMO_SITE_ID`: Matomo site identifier
- `MONITORING_URL`: Netdata monitoring URL
- `BLOB_MAX_SIZE`: Maximum blob size in bytes
- `OAUTH_CLIENT_ID`: OAuth2 client identifier
- `OAUTH_BASE_URL`: OAuth2 provider base URL
- `OAUTH_ISSUER`: Token issuer for validation (required)
- `OAUTH_MODE`: Authentication mode (`oidc` or `rauthy`)
- `LOGIN_MODES`: Array of enabled login modes (`local`, `oauth`, `rauthy`)

### Constants

Defined in `src/constants.ts`:
- `ROLES`: User role array (`admin`, `editor`, `manager`, etc.)
- `CATEGORIES`: ZIM content categories (wiki projects, etc.)
- `CANCELABLE_STATUSES`: Task statuses that can be cancelled
- `MEMORY_VALUES/DISK_VALUES`: Predefined resource arrays (in bytes)
- `WAREHOUSE_PATHS`: Valid warehouse storage paths
- `PERIODICITIES`: Schedule recurrence options

## Authentication

The app supports multiple auth modes configured at runtime:

- **OIDC**: OpenID Connect flow with PKCE (RAuthy, Ory Kratos compatible)
- **RAuthy**: Self-hosted Rust-based OIDC provider with PKCE
- **Local**: Internal username/password authentication

Auth providers implement `AuthProvider` interface (see `src/services/auth/base.ts`).

### Available Auth Providers

| Mode | Provider | Description |
|------|----------|-------------|
| `oidc` | `OAuthOIDCProvider` | OIDC with PKCE flow |
| `rauthy` | `OAuthOIDCProvider` | RAuthy OIDC with PKCE (same provider) |
| `local` | `LocalAuthProvider` | Internal username/password |

**Note:** Session-based authentication (`session` mode) has been removed in favor of OIDC Authorization Code flow with PKCE.

See `src/services/auth/` for implementation details.

## API Integration

- Backend API base: `/v2`
- Uses Axios for HTTP requests
- Configurable via `httpRequest` utility in `src/utils/httpRequest.ts`

## Component Patterns

### State Management

Use Pinia stores for shared state:
```typescript
import { useStoreName } from '@/stores/storeName'

const store = useStoreName()
```

Available stores:
- `auth`: Authentication state and tokens
- `tasks`: Task management and filtering
- `schedules`: Recipe definitions
- `workers`: Worker registration and status
- `users`: User management
- `platforms`: Available scraping platforms
- `offliners`: Scraper configurations
- `languages`: Language definitions
- `blobs`: Arbitrary JSON data storage

### Styling

- Vuetify component props for Material Design
- CSS variables for theming (system theme by default)
- Global styles in `src/assets/styles.css`
- Data table styles in `src/assets/data-table.css`

## Development

### Running in Dev Mode

```bash
yarn dev
```

The dev server proxies `/v2` API requests to the backend automatically.

### Code Quality

- **TypeScript**: Strict mode enabled (`strict: true`)
- **ESLint**: Flat config format (`eslint.config.ts`)
- **Prettier**: Configured in `.prettierrc.json`

### Testing

```bash
yarn test:unit    # Unit tests (Vitest)
yarn test:e2e     # E2E tests (Playwright)
```

## Deployment

### Build for Production

```bash
yarn build
```

### Nginx Configuration

Use `nginx-default.conf` for serving the built app. Key settings:
- SPA fallback to `index.html`
- Static asset caching
- Gzip compression

## Key Patterns

1. **Component naming**: PascalCase (e.g., `ScheduleEditor.vue`)
2. **Store naming**: singular with action (e.g., `useTasksStore`)
3. **API services**: Plural nouns (e.g., `users.ts`, `schedules.ts`)
4. **Type definitions**: Separate `types/` directory with `.ts` files
5. **Utility functions**: Grouped by domain in `utils/`

## API Endpoints (Client-Side)

The frontend consumes these backend endpoints:

| Resource | Endpoint Prefix |
|----------|-----------------|
| Auth     | `/v2/auth/*`    |
| Schedules| `/v2/schedules` |
| Tasks    | `/v2/tasks`     |
| Workers  | `/v2/workers`   |
| Users    | `/v2/users`     |
| Platforms| `/v2/platforms` |
| Offliners| `/v2/offliners` |
| Languages| `/v2/languages` |
| Blobs    | `/v2/blobs`     |

## Troubleshooting

- **Dev server not starting**: Ensure Node.js 24+ and yarn are installed
- **API 401 errors**: Check auth token in Pinia auth store
- **Type errors**: Run `yarn type-check` for detailed errors
- **Build failures**: Clear `node_modules` and `yarn cache` then reinstall

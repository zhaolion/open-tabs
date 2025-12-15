# Open-Tabs (TabAPI)

> Open Tabs In Any Computer

A modern, async-first backend API platform built with FastAPI for authentication and user management.

## Features

- **Email Authentication** - Registration, login, and password reset with verification codes
- **Multi-Factor Verification** - Verification code-based passwordless login
- **JWT Authorization** - Secure token-based authentication
- **Admin Management** - Role-based access control (super_admin, admin, moderator)
- **Async Architecture** - Built on async/await for high performance
- **Database Migrations** - Alembic-powered schema management
- **Redis Caching** - Session and verification code storage
- **CLI Tools** - Administrative commands via Typer

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI, Starlette, Uvicorn |
| **Database** | PostgreSQL, SQLAlchemy 2.0, SQLModel, Alembic |
| **Cache** | Redis |
| **Auth** | PyJWT, Passlib (bcrypt) |
| **Validation** | Pydantic |
| **CLI** | Typer |
| **Testing** | pytest, pytest-asyncio, factory-boy |
| **Code Quality** | Ruff, pre-commit, gitlint |

## Requirements

- Python 3.14+
- PostgreSQL
- Redis
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/zhaolion/open-tabs.git
cd open-tabs
```

### 2. Setup environment

```bash
# One-command setup (recommended)
make setup

# Or manual setup
uv sync
uv run pre-commit install --hook-type commit-msg
uv run pre-commit install
git config commit.template .gitmessage
```

### 3. Configure environment variables

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Key environment variables:

```bash
# Environment
ENV=development                    # development | production | testing
LOGGING_LEVEL=DEBUG

# Database
DATABASE_USER=tabapi_rw
DATABASE_PASSWORD=your_password
DATABASE_URL=127.0.0.1
DATABASE_PORT=5432
DATABASE_NAME=tabapi_dev

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

# Server
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# Email (mock mode for development)
EMAIL_MOCK_MODE=True
```

### 4. Setup database

```bash
# Run migrations
make db-upgrade
```

### 5. Create admin user

```bash
uv run tabapi init admin
```

### 6. Start the server

```bash
# Development server with hot reload
make http_serve

# Or using uv directly
uv run fastapi dev tabapi/http_serve.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/v1/verification-code/send` | Send verification code |
| `POST` | `/auth/v1/register` | Register with email |
| `POST` | `/auth/v1/login` | Login with password |
| `POST` | `/auth/v1/login/verification-code` | Login with verification code |
| `POST` | `/auth/v1/reset-password` | Reset password |
| `GET` | `/api/v1/` | System information |
| `GET` | `/api/v1/health` | Health check |

## Project Structure

```
open-tabs/
├── tabapi/                     # Main application package
│   ├── app/
│   │   ├── core/              # Core infrastructure (config, logger, redis)
│   │   ├── db/                # Database setup (session, base, mixins)
│   │   ├── modules/           # Feature modules
│   │   │   ├── auth/          # Authentication module
│   │   │   │   ├── models.py      # User, Auth, VerificationCode
│   │   │   │   ├── router.py      # API routes
│   │   │   │   ├── service.py     # Business logic
│   │   │   │   ├── schemas.py     # Request/Response models
│   │   │   │   └── utils/         # JWT, password, email utilities
│   │   │   └── system/        # System endpoints
│   │   ├── routes.py          # Route aggregation
│   │   └── setup_app.py       # FastAPI app setup
│   ├── alembic/               # Database migrations
│   ├── http_serve.py          # HTTP server entry
│   └── scripts.py             # CLI commands
├── docs/                       # Documentation
├── main.py                     # Development entry point
├── pyproject.toml             # Project configuration
├── Makefile                   # Build commands
└── alembic.ini                # Migration config
```

## Development

### Available Make Commands

```bash
# Setup
make setup              # Full project setup

# Server
make http_serve         # Start development server

# Database
make db-upgrade         # Run migrations
make db-downgrade       # Rollback one migration
make db-revision msg="description"  # Create new migration
make db-reset           # Reset database

# Code Quality
make check              # Format + lint
make fmt                # Format code
make lint               # Lint code
make pre-commit         # Run all hooks

# Testing
make test               # Run tests
make test-coverage      # Run tests with coverage
```

### Commit Guidelines

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Scopes**: `core`, `auth`, `db`, `router`, `client`, etc.

### Code Quality

- **Ruff** for formatting and linting
- **Pre-commit hooks** for automated checks
- **Type hints** throughout codebase
- **Pydantic** for runtime validation

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
uv run pytest tests/test_auth.py -v
```

Test markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests

## Documentation

- [Developer Guide](docs/develop.md)
- [FastAPI Best Practices](docs/fastapi_best_practices.md)
- [Auth Database Design](docs/feature/auth-database-design.md)
- [Email Auth API Design](docs/feature/email-auth-api-design.md)

## License

TBD

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes following the commit guidelines
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

---

Made with FastAPI

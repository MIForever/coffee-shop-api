# Coffee Shop API — User Management

A production-ready FastAPI backend for user registration, authentication, authorization, and email verification with support for roles, JWT, Celery-based cleanup, and Dockerized deployment.

## Features

### Authentication & Authorization
- User Registration with email/password
- Email Verification (mocked to console in development)
- JWT Auth (access & refresh tokens)
- Role-based Access Control (user & admin)
- Admin-only user management
- /me endpoint to get current user

### Performance & Reliability
- Async architecture (FastAPI + async SQLAlchemy)
- Auto-delete unverified users after 2 days (via Celery)
- Request timeouts and retry mechanisms

### Operations
- Comprehensive health checks for all services
- Structured logging (JSON or plain text)
- Prometheus metrics for monitoring
- Docker multi-stage builds
- Database migrations with Alembic

### Security
- CORS with configurable origins
- Password policies (length, complexity)
- Environment-based configuration

---

## Tech Stack

### Core
- FastAPI + SQLAlchemy (async) + Pydantic
- PostgreSQL (with Alembic for migrations)
- Redis + Celery (background tasks)
- Docker + docker-compose

### Security
- JWT via python-jose
- Password hashing via passlib (bcrypt)
- python-multipart for file uploads

### Monitoring & Observability
- Prometheus metrics
- Structured logging with JSON formatting
- Health check endpoints

### Development & Testing
- pytest with async support
- pytest-asyncio for async test cases
- pytest-cov for test coverage

---

## Getting Started

### Requirements

- Docker + docker-compose
- Python 3.10+ (for local development)
- Redis (for caching and Celery)
- PostgreSQL

### Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd coffee_shop_api

# Copy environment file
cp .env.example .env

# Start with Docker
docker-compose up --build
```

The application will be available at: http://localhost:8000

### Run with Docker (Recommended)

```bash
docker-compose up --build
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health
- Prometheus Metrics: http://localhost:8000/metrics

### API Endpoints

#### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify` - Email verification

#### User Management
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users/` - List users (Admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID (Admin only)
- `PUT /api/v1/users/{user_id}` - Update user (Admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (Admin only)
- `PUT /api/v1/users/{user_id}/role` - Change user role (Admin only)

#### Health Checks
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/db` - Database health check
- `GET /api/v1/health/cache` - Redis health check
- `GET /api/v1/health/full` - Full system health check

### Development Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Running Tests

Run the test suite with coverage:

```bash
pytest -v --cov=app --cov-report=term-missing
```

For basic functionality testing:

```bash
python test_basic.py
```

### Database Migrations

1. Create a new migration:
   ```bash
   alembic revision --autogenerate -m "description of changes"
   ```

2. Apply migrations:
   ```bash
   alembic upgrade head
   ```

## Monitoring & Observability

### Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Basic health status |
| `GET /api/v1/health/db` | Database health check |
| `GET /api/v1/health/cache` | Redis cache health check |
| `GET /api/v1/health/full` | Comprehensive health check |

### Metrics

Prometheus metrics are available at `/metrics` and include:
- Request counts and latencies
- Error rates
- Database query metrics
- Cache hit/miss ratios

## Security

### Password Policies
- Minimum length: 8 characters
- Requires uppercase, lowercase, numbers, and special characters

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database migrations with [Alembic](https://alembic.sqlalchemy.org/)
- Background tasks with [Celery](https://docs.celeryq.dev/)
- Monitoring with [Prometheus](https://prometheus.io/)
```

---

## Project Structure

```
.
├── app/
│   ├── api/           # API routes
│   ├── core/          # Configuration, auth, celery
│   ├── db/            # Database session
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── tasks/         # Celery tasks
├── alembic/           # Database migrations
├── tests/             # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔐 Auth Overview

| Endpoint          | Description                         |
|------------------|-------------------------------------|
| `POST /auth/signup` | Register a new user               |
| `POST /auth/login`  | Get access + refresh tokens       |
| `POST /auth/refresh`| Refresh access token              |
| `POST /auth/verify` | Verify email                      |

---

## 👤 User Management

| Endpoint                  | Access      | Description                          |
|---------------------------|-------------|--------------------------------------|
| `GET /me`                 | Authenticated | Get current user's info           |
| `GET /users`              | Admin only  | List all users                       |
| `GET /users/{id}`         | Admin only  | Get specific user                    |
| `PATCH /users/{id}`       | User/Admin  | Update own info or any (if admin)    |
| `PATCH /users/{id}/role`  | Admin only  | Promote/demote user                  |
| `DELETE /users/{id}`      | Admin only  | Delete user                          |

---

## 📧 Email Verification

- After registration, user is **unverified**
- A mock verification token is printed to the console
- Send a `POST /auth/verify` with that token to verify the account

> ⚠ In production, integrate `FastAPI-Mail`, SendGrid, or SMTP.

---

## 🧹 Auto-deletion of unverified users

- Runs via Celery task
- Users who aren’t verified within 48 hours are deleted
- Triggered via:
```bash
celery -A app.core.celery.celery_app worker --loglevel=info
```

---

## ⚙️ Configuration

## 🔧 Environment Variables

All settings are loaded from `.env`. Copy `.env.example` to `.env` and update the values as needed.

### Database

```env
# PostgreSQL database connection
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=coffee_shop
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}/${POSTGRES_DB}
```

### Authentication

```env
# JWT Settings
JWT_SECRET_KEY=supersecretkey
JWT_REFRESH_SECRET_KEY=supersecretrefreshkey
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Email (SMTP)

```env
# SMTP settings for email
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.example.com
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@example.com
EMAILS_FROM_NAME="Coffee Shop"
EMAIL_VERIFICATION_ENABLED=true
```

### Redis & Celery

```env
# Redis connection for Celery and caching
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# Celery configuration
CELERY_BROKER_URL=${REDIS_URL}
CELERY_BACKEND_URL=${REDIS_URL}
CELERY_TASK_ALWAYS_EAGER=False  # Set to True for testing
```

### Application Settings

```env
# Application settings
PROJECT_NAME="Coffee Shop API"
API_VERSION=1.0.0
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
LOG_FORMAT=json  # json or plain

# CORS (comma-separated list of origins, or "*" for all)
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend.com"]

# Security
SECRET_KEY=supersecretappkey
ALLOWED_HOSTS=["*"]  # In production, specify exact hosts

# Rate limiting
RATE_LIMIT=100  # requests per minute
RATE_LIMIT_AUTH=5  # requests per minute for auth endpoints
RATE_LIMIT_ADMIN=30  # requests per minute for admin endpoints
```

---

## 🧪 Tests (TODO)

Test coverage recommended:

- [ ] Register/login/verify flow
- [ ] `/me` endpoint
- [ ] Admin role protection
- [ ] Refresh tokens
- [ ] Celery token deletion

Run with:

```bash
pytest
```

---

## 🛠 Admin User Setup

To promote a user to admin, use:

```http
PATCH /users/{id}/role
{
  "role": "admin"
}
```

Or create a CLI script to seed one manually (optional).

---

## 🧱 Migrations

Using Alembic:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

## 📜 License

MIT — free to use, modify, and distribute.

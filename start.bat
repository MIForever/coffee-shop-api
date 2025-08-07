@echo off
echo Coffee Shop API - Quick Start
echo ==============================

docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

if not exist .env (
    echo Creating .env file from template...
    copy env.example .env
    echo .env file created. Please review and update the configuration if needed.
) else (
    echo .env file already exists.
)

echo Starting Coffee Shop API...
echo This will start:
echo   - FastAPI application (port 8000)
echo   - PostgreSQL database (port 5432)
echo   - Redis cache (port 6379)
echo   - Celery worker
echo   - Celery beat scheduler
echo.

docker-compose up --build

echo.
echo Coffee Shop API is now running!
echo.
echo Available endpoints:
echo   - API Documentation: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/api/v1/health/
echo   - Metrics: http://localhost:8000/metrics
echo.
echo To stop the application, press Ctrl+C or run:
echo    docker-compose down
echo.
echo To test the API, run:
echo    python test_basic.py
pause

#!/bin/bash

echo "Coffee Shop API - Quick Start"
echo "=============================="

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo ".env file created. Please review and update the configuration if needed."
else
    echo ".env file already exists."
fi

echo "Starting Coffee Shop API..."
echo "This will start:"
echo "  - FastAPI application (port 8000)"
echo "  - PostgreSQL database (port 5432)"
echo "  - Redis cache (port 6379)"
echo "  - Celery worker"
echo "  - Celery beat scheduler"
echo ""

docker-compose up --build

echo ""
echo "Coffee Shop API is now running!"
echo ""
echo "Available endpoints:"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/api/v1/health/"
echo "  - Metrics: http://localhost:8000/metrics"
echo ""
echo "To stop the application, press Ctrl+C or run:"
echo "   docker-compose down"
echo ""
echo "To test the API, run:"
echo "   python test_basic.py"

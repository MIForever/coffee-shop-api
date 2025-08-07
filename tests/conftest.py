import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event

# Set test environment before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["POSTGRES_DB"] = "test_coffee_shop"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"

from app.core.config import settings
from app.models.base import Base
from app.db.deps import get_db
from app.main import app as _app

# Use a test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_coffee_shop")

# Create test engine and session
engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create and drop test database tables."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session with a rollback at the end of the test.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Begin a nested transaction
    nested = await connection.begin_nested()
    
    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @event.listens_for(session.sync_session, 'after_transaction_end')
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.sync_connection.begin_nested()
    
    yield session
    
    # Cleanup
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest.fixture(scope="function")
async def client(db_session) -> Generator[TestClient, None, None]:
    """
    Create a test client that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
        finally:
            pass
    
    _app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(_app) as test_client:
        yield test_client
    
    _app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Fixture to get the FastAPI application."""
    return _app

# Add fixtures for test data
@pytest.fixture
def test_user():
    """Fixture to create a test user."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }

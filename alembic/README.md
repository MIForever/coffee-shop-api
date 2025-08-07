# Alembic Database Migrations

This directory contains Alembic migration scripts for the Coffee Shop API project.

## Usage

1. **Initialize Alembic (if not done):**
   ```bash
   alembic init alembic
   ```

2. **Edit `alembic.ini` and `alembic/env.py` as needed.**

3. **Create a new migration:**
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```

4. **Apply migrations:**
   ```bash
   alembic upgrade head
   ```

## References
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)

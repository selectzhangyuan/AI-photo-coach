#!/bin/bash
set -e

echo "Running database migrations..."
python -c "from app.core.database import init_db; init_db()"
echo "Migrations complete. Starting uvicorn..."

exec uvicorn app.main:app --host 0.0.0.0 --port 8000

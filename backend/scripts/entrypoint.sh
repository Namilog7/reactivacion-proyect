#!/bin/sh
set -e

echo "[backend] Aplicando migraciones..."
alembic upgrade head

echo "[backend] Verificando datos semilla..."
python -m app.seed

echo "[backend] Iniciando API en 0.0.0.0:${BACKEND_PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-${BACKEND_PORT:-8000}}"
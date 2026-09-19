# Docker Compose

## Servicios

| Servicio | Imagen base | Expuesto al host | Puerto interno | Rol |
|----------|-------------|------------------|----------------|-----|
| `db` | `postgres:16-alpine` | No | `5432` | PostgreSQL 16 |
| `backend` | `python:3.12-slim` (build) | No | `8000` | API FastAPI |
| `frontend` | `nginx:1.27-alpine` (build) | **`${FRONTEND_PORT:-8080}` → `80`** | `80` | SPA + proxy `/api` |

### Dependencias y arranque

```
frontend ──(no depende, sirve en cuanto está)────┐
backend  ──depends_on: db (service_healthy)──────┤
db        ──healthcheck: pg_isready -U cobranzas──┘
```

- `db` no publica puertos al host; PostgreSQL escucha en `:5432` y es alcanzable por los demás servicios de la red interna de Compose (`db:5432`), que es como lo usa `DATABASE_URL`.
- `backend` arranca con `scripts/entrypoint.sh`:
  1. `alembic upgrade head` (migraciones).
  2. `python -m app.seed` (datos de desarrollo, idempotente).
  3. `exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-${BACKEND_PORT:-8000}}"`.
- `frontend` es una imagen multi-etapa: compila con Node 20 (`Vite build`) y copia `dist/` + `nginx.conf` a Nginx.

## Redes

- Red única por defecto de Compose. Los nombres de servicio (`db`, `backend`, `frontend`) son resolubles como DNS entre contenedores; por eso `DATABASE_URL` usa el host `db` y el proxy local usaría `http://backend:8000/`.

## Volúmenes

| Volumen | Montado en | Contenido |
|---------|------------|-----------|
| `pgdata` | `db:/var/lib/postgresql/data` | Datos de PostgreSQL (**crítico**) |
| `uploads_data` | `backend:/data/uploads` | Archivos subidos. **Reservado**: la carga por operador procesa en memoria y no persiste archivos; lo usaría el módulo de conciliación (desactivado). |

Ambos son volúmenes con nombre (declarados en la sección `volumes:`), por lo que sobreviven a `docker compose down` y `docker compose build`. Se borran solo con `docker compose down -v`.

## Comandos útiles

```bash
docker compose up -d --build        # construir + levantar
docker compose build                # reconstruir imágenes
docker compose up -d                # levantar (reutiliza imágenes)
docker compose ps                   # estado + healthcheck
docker compose logs -f backend      # logs en vivo
docker compose exec backend pytest -q   # tests (usa cobranzas_test)
docker compose exec db psql -U cobranzas -d cobranzas
docker compose down                 # detener (conserva volúmenes)
docker compose down -v              # detener Y BORRAR datos (¡solo desde cero!)
docker compose restart backend      # reiniciar un servicio
```

## Configuración por servicio (resumen)

- `db`: lee `POSTGRES_USER/PASSWORD/DB`; healthcheck `pg_isready`; volumen `pgdata`.
- `backend`: lee `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `UPLOAD_DIR`, `BACKEND_PORT`; volumen `uploads_data`; `restart: unless-stopped`; depende de `db` sano.
- `frontend`: publica `FRONTEND_PORT→80`; `VITE_API_BASE` definida pero **no consumida** por el código (el prefijo `/api` es fijo en `src/api/client.ts`).

## Verificación de consistencia

Para confirmar que lo que levanta Compose coincide con la documentación:

```bash
docker compose config        # renderiza la configuración efectiva (valores de .env incluidos)
docker compose config --services
```

## Actualización de imágenes base

El proyecto fija versiones mayores en los `Dockerfile` (`node:20-alpine`, `python:3.12-slim`, `postgres:16-alpine`, `nginx:1.27-alpine`) y menores en `requirements*.txt`. Actualizar imágenes base es una tarea de mantenimiento **manual y controlada** (ver `mantenimiento.md`).
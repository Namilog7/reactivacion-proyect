# Configuración

## Dónde se define cada variable

| Variable | Default | Se lee en | Descripción |
|----------|---------|-----------|-------------|
| `POSTGRES_USER` | `cobranzas` | `docker-compose.yml` | Usuario de PostgreSQL (servicio `db`) |
| `POSTGRES_PASSWORD` | `cobranzas` | `docker-compose.yml` | Contraseña de PostgreSQL (**cambiar**) |
| `POSTGRES_DB` | `cobranzas` | `docker-compose.yml` | Nombre de la base |
| `DATABASE_URL` | `postgresql+psycopg://cobranzas:cobranzas@db:5432/cobranzas` | `backend/app/config.py`, `alembic/env.py`, `tests/conftest.py` | Cadena SQLAlchemy (driver `psycopg` v3) |
| `SECRET_KEY` | `clave-insegura-solo-para-desarrollo` | `backend/app/config.py` | Clave HMAC de firma de JWT (**cambiar en producción**) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | `backend/app/config.py` | Expiración del JWT en minutos |
| `UPLOAD_DIR` | `/data/uploads` | `backend/app/config.py` | Ruta de archivos dentro del contenedor (reservado) |
| `BACKEND_PORT` | `8000` | `backend/scripts/entrypoint.sh` | Puerto de uvicorn en el contenedor |
| `PORT` | — | `backend/scripts/entrypoint.sh` | Si está definida (plataformas como Render), **tiene prioridad** sobre `BACKEND_PORT` |
| `FRONTEND_PORT` | `8080` | `docker-compose.yml` | Puerto del frontend expuesto en el host |
| `VITE_API_BASE` | `/api` | `docker-compose.yml` | **Reservada**: el código fija `/api` en `frontend/src/api/client.ts` y no la consume |

> Precedencia real del puerto del backend: `PORT` (plataforma) → `BACKEND_PORT` → `8000`.
> Precedencia de configuración en el backend: variables de entorno **>** `.env` **>** defaults de `app/config.py` (pydantic-settings).

## Red interna y puertos

- `db`: PostgreSQL escucha en `:5432`, **no expuesto al host**. El único cliente es el backend por la red interna de Compose.
- `backend`: uvicorn escucha en `:8000`, **no expuesto al host**. Lo alcanza únicamente el Nginx del frontend (y el CLI con `docker compose exec`).
- `frontend`: Nginx escucha `:80` en el contenedor, publicado en el host como **`FRONTEND_PORT`** (default `8080`).

Si necesitas exponer PostgreSQL o el backend al host (solo para depuración puntual), agrégalo temporalmente en `docker-compose.yml`, por ejemplo:

```yaml
services:
  db:
    ports:
      - "5432:5432"
```

**No lo mantengas así en producción** (ver `seguridad.md`).

## Generación de secretos

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # SECRET_KEY
# o en PowerShell:
# [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Max 256 }))

# Contraseña de PostgreSQL:
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

Inyectar `SECRET_KEY`, `POSTGRES_PASSWORD` y `DATABASE_URL` en `.env` **antes** del primer `docker compose up`. Cambiarlos después invalida los tokens emitidos (JWT) o exige recrear el contenedor `db`.

## Checklist de producción

- [ ] `SECRET_KEY` aleatoria (nunca el default de `config.py`).
- [ ] `POSTGRES_PASSWORD` y usuario propios (nunca `cobranzas/cobranzas`).
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` ajustado a la política de la empresa (ej. `480` mín; valores menores reducen la ventana de un token robado).
- [ ] Usuarios seed deshabilitados o con contraseñas propias.
- [ ] Acceso a la app por **HTTPS** (terminar TLS en un reverse proxy del host; ver `despliegue.md`).
- [ ] Backend/frontend alcanzados por el mismo origen (evitar configuración CORS; ver `seguridad.md`).
- [ ] Backups automáticos configurados (`base-de-datos.md`).
- [ ] Revisión de `auditoria-tecnica.md` y deuda priorizada.
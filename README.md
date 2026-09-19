# Sistema de Gestión de Cobranzas

Aplicación web interna para el seguimiento de **gestiones de cobranza** por período, **carga de archivos XLSX por operador** y control de **alertas** por incumplimiento de reglas de negocio (p. ej. "pagó sin nota de crédito", "pagó sin desbloqueo").

Es un monorepo con dos entregables ejecutables vía Docker Compose:

- **frontend** — SPA React (Vite + TypeScript) servida por Nginx. También actúa como *reverse proxy* de la API bajo el prefijo `/api`.
- **backend** — API REST FastAPI (Python 3.12 + SQLAlchemy 2 + Alembic) sobre PostgreSQL 16. Aplica migraciones y datos de desarrollo automáticamente al arrancar.

**Stack**: React 18 · Vite 5 · TypeScript 5.6 · Nginx 1.27 · FastAPI 0.115 · SQLAlchemy 2.0 · Alembic 1.14 · PostgreSQL 16 · Docker Compose.

---

## Tabla de contenido

- [Requisitos](#requisitos)
- [Puesta en marcha](#puesta-en-marcha)
- [Usuarios de prueba](#usuarios-de-prueba-seed)
- [Configuración](#configuración)
- [Comandos útiles](#comandos-útiles)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Documentación](#documentación)
- [Estado del producto](#estado-del-producto)

---

## Funcionalidades

- Autenticación con roles **SUPERVISOR** y **OPERADOR** (JWT + bcrypt).
- ABM de usuarios, períodos y catálogos de tipos de operación.
- ABM de gestiones por cliente/período con control de acceso (un operador solo ve y edita sus gestiones), unicidad `(cliente, período)` e **historial de cambios** auditable.
- Reglas de alerta centralizadas en el backend (nivel `NINGUNA` / `ALERTA` / `CRITICA`) evaluadas por gestión. El frontend solo las renderiza.
- Carga por operador: el supervisor sube un `.xlsx` con números de cliente y un motivo; el backend actualiza los flags de las gestiones correspondientes (idempotente, sin persistir el archivo).
- Dashboard con métricas por operador (OPERADOR) y resumen global por período (SUPERVISOR).
- **Modo demo/sandbox**: acceso anónimo y de **solo lectura** con datos de ejemplo respaldados por **Redis** y sesiones que expiran solas (TTL absoluto). Detalle en [docs/sandbox.md](docs/sandbox.md).
- API documentada (OpenAPI/Swagger) accesible desde el frontend en `/api/docs`.

## Arquitectura

```
Navegador
   │  http://<host>:8080   (http 80 dentro del contenedor frontend)
   ▼
Nginx (frontend container)
   │  estático React + proxy /api → backend
   ▼
Backend FastAPI (container interno :8000)
   │  JWT (OAuth2 password), rutas montadas en la raíz
   ▼
PostgreSQL 16 (container interno :5432)
   ▼
volúmenes Docker: pgdata (datos), uploads_data (reservado)
```

Hay **dos modos de conexión API** que difieren solo en `frontend/nginx.conf`:

| Modo | `proxy_pass` en `frontend/nginx.conf` | Uso |
|------|----------------------------------------|-----|
| **Backend externo** (configuración actual) | `https://reactivacion-backend.onrender.com/` con `proxy_ssl_server_name on` | Entorno de prueba con la API desplegada en Render. Ve a `docs/despliegue.md`. |
| **Backend en el mismo host** (recomendado para producción) | `http://backend:8000/` | Todo el sistema corre en la misma máquina con Compose. Ve a `docs/despliegue.md` (modo recomendado). |

> El backend monta sus rutas en la raíz (`/auth/login`, `/gestiones`, …); el prefijo `/api` lo elimina Nginx (y Vite en desarrollo). Si usas el modo externo, es obligatorio enviar `Host` y **SNI** (`proxy_ssl_server_name on`) — sin SNI, Cloudflare/Render responde `handshake_failure` y Nginx devuelve **502**. Detalle en `docs/troubleshooting.md`.

## Requisitos

- Docker Engine + Docker Compose (build de frontend vía Node dentro del contenedor; **no** hace falta Node local).
- Puertos libres: `8080` en el host (configurable con `FRONTEND_PORT`). El backend y la BD **no** se exponen al host.

## Puesta en marcha

```bash
cp .env.example .env      # ajusta los valores (ver "Configuración")
docker compose up -d --build
```

Al arrancar, el backend aplica las migraciones (Alembic), ejecuta el seed idempotente y levanta uvicorn. La aplicación queda en:

- Frontend: <http://localhost:8080>
- API (Swagger): <http://localhost:8080/api/docs>
- Healthcheck: <http://localhost:8080/api/health>

Verificación rápida:

```bash
docker compose ps                 # db healthy, backend y frontend running
docker compose logs backend       # espera "[seed] OK"
curl http://localhost:8080/api/health
```

Detalles en [docs/instalacion.md](docs/instalacion.md) y [docs/manual-instalacion.md](docs/manual-instalacion.md).

## Usuarios de prueba (seed)

| Usuario    | Contraseña    | Rol        |
|------------|---------------|------------|
| supervisor | supervisor123 | SUPERVISOR |
| operador1  | operador123   | OPERADOR   |
| operador2  | operador123   | OPERADOR   |

> **Obligatorio en cualquier entorno que no sea desarrollo:** cambiar contraseñas y crear usuarios propios.

## Configuración

`.env` | Para producción | Variables |
|---|---|---|
`POSTGRES_USER/PASSWORD/DB` | usuario/clave/base de PostgreSQL | PostgreSQL 16 del contenedor `db` |
`DATABASE_URL` | conexión SQLAlchemy (driver `psycopg`) | backend |
`SECRET_KEY` | firma de JWT — **generar aleatoria** | backend |
`ACCESS_TOKEN_EXPIRE_MINUTES` | expiración del token (default `480`) | backend |
`UPLOAD_DIR` | directorio de archivos (default `/data/uploads`) | backend |
`BACKEND_PORT` | puerto uvicorn interno (default `8000`) | backend |
`REDIS_URL` | conexión Redis (default `redis://redis:6379`) | backend (modo demo) |
`SANDBOX_TTL_SECONDS` | TTL absoluto de las sesiones demo en segundos (default `3600`) | backend (modo demo) |
`FRONTEND_PORT` | puerto del frontend en el host (default `8080`) | frontend |

> `DATABASE_URL` usa el host `db` porque el backend corre en la red interna de Compose. Si el backend va a otra infraestructura (p. ej. Render), apunta la URL ahí.

Documentación completa: [docs/configuracion.md](docs/configuracion.md) y `docs/despliegue.md`.

## Comandos útiles

```bash
# Logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Tests (usa una base PostgreSQL separada cobranzas_test)
docker compose exec backend pytest -q

# Migrar/verificar que no hay cambios pendientes
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "verif"

# Consola PostgreSQL
docker compose exec db psql -U cobranzas -d cobranzas

# Re-aplicar datos de desarrollo (idempotente)
docker compose exec backend python -m app.seed

# Respaldar/restaurar la base (ver docs/base-de-datos.md)
docker compose exec db pg_dump -U cobranzas -d cobranzas | gzip > cobranzas-$(date +%F).sql.gz

# Actualizar la aplicación
git pull && docker compose build && docker compose up -d
```

## Estructura del proyecto

```
├── .env.example          # plantilla de configuración
├── docker-compose.yml    # orquestación: db + redis + backend + frontend
├── backend/
│   ├── Dockerfile        # python:3.12-slim
│   ├── scripts/entrypoint.sh  # alembic upgrade + seed + uvicorn
│   ├── alembic/          # migraciones (Alembic)
│   ├── requirements.txt / requirements-dev.txt
│   ├── app/
│   │   ├── domain/       # reglas de negocio puras (alertas, motivos de carga, enums)
│   │   ├── models/       # SQLAlchemy (gestiones, clientes, periodos, historial)
│   │   ├── schemas/      # Pydantic (DTOs)
│   │   ├── repositories/ # acceso a datos
│   │   ├── services/     # lógica de aplicación (autenticación, gestión, carga, historial)
│   │   ├── sandbox/      # modo demo: store Redis, seed, reader, deps (solo lectura)
│   │   ├── routers/      # API REST (auth, usuarios, periodos, catalogos, gestiones, cargas, dashboard)
│   │   ├── importer/     # parsers de XLSX
│   │   ├── core/         # seguridad (JWT), dependencias, configuración
│   │   └── main.py       # FastAPI app (v0.2.0)
│   └── tests/            # suite pytest (conftest + escenarios)
└── frontend/
    ├── Dockerfile        # build node:20-alpine → nginx:1.27-alpine
    ├── nginx.conf        # estático + proxy /api
    ├── vite.config.ts    # dev server + proxy /api → localhost:8000
    └── src/              # React + Vite + TypeScript
```

## Documentación

| Tema | Documento |
|------|-----------|
| Arquitectura, capas y decisiones | [docs/arquitectura.md](docs/arquitectura.md) |
| Instalación rápida | [docs/instalacion.md](docs/instalacion.md) |
| Manual de instalación (paso a paso, finalista) | [docs/manual-instalacion.md](docs/manual-instalacion.md) |
| Configuración y variables de entorno | [docs/configuracion.md](docs/configuracion.md) |
| Despliegue (modo local y con backend externo) | [docs/despliegue.md](docs/despliegue.md) |
| Docker Compose (topología, volúmenes, operación) | [docs/docker.md](docs/docker.md) |
| Base de datos y migraciones | [docs/base-de-datos.md](docs/base-de-datos.md) · [docs/modelo-datos.md](docs/modelo-datos.md) |
| Seguridad | [docs/seguridad.md](docs/seguridad.md) |
| Mantenimiento y operación | [docs/mantenimiento.md](docs/mantenimiento.md) |
| Solución de problemas | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Desarrollo y extensión | [docs/desarrollo.md](docs/desarrollo.md) |
| API | [docs/api.md](docs/api.md) |
| Flujo de carga por operador | [docs/cargas.md](docs/cargas.md) |
| Modo demo/sandbox | [docs/sandbox.md](docs/sandbox.md) |
| Manual de usuario | [docs/manual-usuario.md](docs/manual-usuario.md) |
| Auditoría técnica | [docs/auditoria-tecnica.md](docs/auditoria-tecnica.md) |

## Estado del producto

- Fases 1-4 del requerimiento implementadas (login/roles, ABM usuarios/períodos/tipos, gestiones con historial y alertas, control de acceso por rol).
- **Carga por operador** implementada (sustituye al flujo de conciliación). No persiste auditoría ni archivos.
- El módulo de **conciliación** está desactivado (sin API ni UI); sus tablas se conservan en la BD sin uso.
- Ver [docs/auditoria-tecnica.md](docs/auditoria-tecnica.md) para fortalezas, riesgos y deuda técnica detectada.
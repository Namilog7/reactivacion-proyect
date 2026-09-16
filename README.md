# Sistema de Gestión de Cobranzas

Aplicación web interna para el seguimiento de gestiones de cobranza, carga de archivos XLSX por operador y control de alertas por incumplimiento de reglas de negocio.

**Stack**: FastAPI (Python) + PostgreSQL + React (Vite) + Nginx, orquestado con Docker Compose.

---

## Requisitos

- Docker + Docker Compose (build de frontend vía Node dentro del contenedor; no hace falta Node local).
- Puerto `8080` libre (configurable con `FRONTEND_PORT`).

## Puesta en marcha

```bash
docker compose up -d --build
```

El `backend` aplica migraciones (Alembic) y el seed de datos al arrancar. La aplicación queda en:

- Frontend: http://localhost:8080
- API (Swagger): http://localhost:8080/api/docs

### Usuarios de prueba (seed)

| Usuario     | Contraseña     | Rol        |
|-------------|----------------|------------|
| supervisor  | supervisor123  | SUPERVISOR |
| operador1   | operador123    | OPERADOR   |
| operador2   | operador123    | OPERADOR   |

## Comandos útiles

```bash
# Logs
docker compose logs -f backend

# Tests (usa una base PostgreSQL separada cobranzas_test)
docker compose exec backend pytest -q

# Migración manual y verificación de que no hay cambios pendientes
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "verif"

# Consola de Django/psql
docker compose exec db psql -U cobranzas -d cobranzas
```

## Estructura del proyecto

```
backend/
  app/
    domain/        # Reglas de negocio puras (alertas, motivos de carga, enums)
    models/        # SQLAlchemy (gestiones, clientes, periodos, historial)
    schemas/       # Pydantic (DTOs de entrada/salida)
    repositories/  # Acceso a datos
    services/      # Lógica de aplicación (gestión, carga, historial, usuario)
    routers/       # API REST
    importer/      # Parser de XLSX (encabezados y valores normalizados)
    core/          # Seguridad (JWT), dependencias
    alembic/       # Migraciones
    tests/         # Suite (conftest + escenarios)
  frontend/
    src/           # React + Vite + TypeScript
```

## Fases del requerimiento cubiertas

- **Fase 1-3**: login con roles, ABM de usuarios, gestión de períodos y tipos de operación.
- **Fase 4**: CRUD de gestiones con control de acceso por rol, historial de cambios y reglas de alerta (sección 7).
- **Carga por operador**: el supervisor sube un archivo XLSX por operador indicando un motivo (pago y desbloqueo, pago sin desbloqueo, deuda sin NC, deuda sin NC ni desbloqueo); el sistema actualiza las gestiones de ese operador en el período vigente. No persiste auditoría.
- El módulo de conciliación quedó desactivado por ahora (API y UI retiradas; las tablas se conservan).

Detalles en [`docs/`](docs/).
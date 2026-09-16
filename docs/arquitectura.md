# Arquitectura

## Visión general

```
Browser
   │  http://localhost:8080
   ▼
Nginx (frontend container, :80)
   │  estático React + proxy /api → backend
   ▼
FastAPI (backend container, :8000)
   │  JWT (OAuth2 password), rutas montadas en la raíz
   ▼
PostgreSQL 16 (db container)
   │  esquema "cobranzas" (migrado por Alembic)
   ▼
volúmenes: pgdata (datos), uploads_data (archivos XLSX subidos)
```

- El frontend llama a la API con prefijo `/api`. Nginx lo elimina (`proxy_pass http://backend:8000/;`) porque el backend monta sus rutas en la raíz (`/auth/login`, `/gestiones`, …). En desarrollo, `vite.config.ts` hace el mismo rewrite.
- Las cargas por operador se procesan en memoria (lectura del XLSX, actualización de flags y commit); no se persiste el archivo ni auditoría.
- El `entrypoint.sh` del backend ejecuta `alembic upgrade head`, el seed idempotente y arranca uvicorn.

## Capas (backend)

| Capa | Responsabilidad |
|------|-----------------|
| `domain/` | Reglas de negocio puras, sin dependencias de infraestructura: `alertas.py` (reglas 1-4 de la sección 7), `cargas.py` (motivos de carga por operador), `enums.py`. |
| `models/` | Definiciones SQLAlchemy `Mapped`. Sin lógica de negocio. |
| `repositories/` | Queries. Los servicios no construyen SQL directamente. |
| `services/` | Casos de uso (crear/actualizar gestiones, carga por operador, historial, autenticación, usuarios). |
| `schemas/` | Pydantic v2. `ORMModel` centraliza un validador `UUID → str` para todas las respuestas. |
| `routers/` | Capa HTTP (respuestas, permisos). Delgado: delega en servicios. |
| `importer/` | Parsers de XLSX: `xlsx_parser.py` (cliente + tipo, para conciliación) y `clientes_parser.py` (solo números, para carga por operador). Normalizan encabezados y valores. |

## Decisiones clave

- **Reglas de alerta en un solo lugar**: el backend evalúa `alertas` por gestión (nivel, flags por celda, mensajes) y el frontend solo renderiza. Nunca se duplican en JS.
- **Motivos de carga por operador** (`domain/cargas.py`): cada motivo define qué campos de las gestiones del operador se actualizan (p. ej. `PAGO_DESBLOQUEO` → `pago = True`, `desbloqueado = True`; `DEUDA_SIN_NC` → `tiene_nc = False`). La carga se limita a gestiones existentes de ese operador en el período.
- **Columnas enum**: la BD usa enums a nivel base (p. ej. `campo_cambio_enum` con valores minúscula). El ORM las declara como `postgresql.ENUM(..., create_type=False)` de paso directo (string) y el dominio normaliza valores; así el nombre del miembro Python no interfiere con el valor de la BD.
- **Autenticación**: OAuth2 password + JWT. El operador sólo ve y edita sus gestiones; el supervisor gestiona períodos, usuarios y cargas por operador.
- **Desactivación de la conciliación**: se retiraron la UI y la API (`/conciliaciones`) y la carga no persiste auditoría; las tablas de conciliación se conservan en la BD sin uso.
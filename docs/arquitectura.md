# Arquitectura

> Lectura recomendada en paralelo con: `base-de-datos.md`, `seguridad.md` y `despliegue.md`.

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
PostgreSQL 16 (db container, :5432)
   │  esquema "cobranzas" (migrado por Alembic)
   ▼
volúmenes: pgdata (datos), uploads_data (archivos XLSX; reservado)
```

- El frontend llama a la API con prefijo `/api`. Nginx lo elimina porque el backend monta sus rutas en la raíz (`/auth/login`, `/gestiones`, …). En desarrollo, `vite.config.ts` hace el mismo rewrite (proxy `/api` → `localhost:8000`).
- **Conexión del proxy según el entorno** (define `frontend/nginx.conf`):

  | Modo | `proxy_pass` | Detalle |
  |------|--------------|---------|
  | Backend externo (actual) | `https://reactivacion-backend.onrender.com/` | Requiere `proxy_ssl_server_name on` + `proxy_ssl_name` + `Host` manual porque el destino es Cloudflare/Render. Sin SNI el handshake falla (`SSL alert number 40`) y Nginx devuelve 502. |
  | Backend local (producción recomendada) | `http://backend:8000/` | Todo en la misma red interna de Compose. No hace falta SNI ni Host manual. |

  Ambas variantes usan el *trailing slash* (`https://…/` o `http://backend:8000/`), que es lo que elimina el prefijo `/api`. Si se omite el slash, el upstream recibe `/api/…` y el backend devuelve 404.

- Las cargas por operador se procesan en memoria (lectura del XLSX, actualización de flags y commit); **no** se persiste el archivo ni auditoría.
- El `entrypoint.sh` del backend ejecuta `alembic upgrade head`, el seed idempotente y arranca uvicorn (`PORT` → `BACKEND_PORT` → `8000`).

## Capas (backend)

| Capa | Responsabilidad |
|------|-----------------|
| `domain/` | Reglas de negocio puras, sin dependencias de infraestructura: `alertas.py` (reglas 1-4), `cargas.py` (motivos de carga por operador), `conciliacion_reglas.py` (estrategias; módulo desactivado), `enums.py`. |
| `models/` | Definiciones SQLAlchemy `Mapped`. Sin lógica de negocio. |
| `repositories/` | Queries. Los servicios no construyen SQL directamente. |
| `services/` | Casos de uso (crear/actualizar gestiones, carga por operador, historial, autenticación, usuarios). |
| `schemas/` | Pydantic v2. `ORMModel` centraliza un validador `UUID → str` para todas las respuestas. |
| `routers/` | Capa HTTP (respuestas, permisos). Delgado: delega en servicios. |
| `importer/` | Parsers de XLSX: `xlsx_parser.py` (cliente + tipo, para conciliación) y `clientes_parser.py` (solo números, para la carga por operador). Normalizan encabezados y valores. |

## Decisiones clave

- **Reglas de alerta en un solo lugar**: el backend evalúa `alertas` por gestión (nivel, flags por celda, mensajes) y el frontend solo renderiza. Nunca se duplican en JS.
- **Motivos de carga por operador** (`domain/cargas.py`): cada motivo define qué campos de las gestiones del operador se actualizan (p. ej. `PAGO_DESBLOQUEO` → `pago = True` y `desbloqueado = True`; `DEUDA_SIN_NC` → `tiene_nc = False`). La carga se limita a gestiones existentes de ese operador en el período; las filas sin gestión se ignoran (`sin_gestion`). Es idempotente: solo registra cambios cuando el valor difiere.
- **Columnas enum**: la BD usa enums a nivel base (p. ej. `campo_cambio_enum` con valores en minúscula). El ORM las declara como `postgresql.ENUM(..., create_type=False)` de paso directo (string) y el dominio normaliza valores; así el nombre del miembro Python no interfiere con el valor de la BD.
- **Autenticación**: OAuth2 password + JWT (HS256). El operador solo ve y edita sus gestiones; el supervisor gestiona períodos, usuarios y cargas por operador.
- **Desactivación de la conciliación**: se retiraron la UI y la API (`/conciliaciones`) y la carga por operador no persiste auditoría; las tablas de conciliación se conservan en la BD sin uso.

## Flujo de una solicitud (ejemplo: listar gestiones)

1. `GET /api/gestiones?periodo_id=…` llega a Nginx (frontend).
2. Nginx quita `/api` → `GET /gestiones?periodo_id=…` al backend.
3. El router valida permisos (`get_current_usuario`, y dueño/supervisor en el caso de detalle).
4. El servicio consulta vía repositorio y calcula `alertas` con `domain/alertas.evaluar_alertas`.
5. El schema de salida (Pydantic v2) serializa con UUID → `str` y devuelve JSON.

## Modos de ejecución

| Modo | Cómo | Notas |
|------|------|-------|
| Producción / demo | `docker compose up -d --build` | Compose levanta `db` + `backend` + `frontend`. |
| Desarrollo frontend | `cd frontend && pnpm install && pnpm dev` | Vite proxya `/api` → `localhost:8000` (requiere backend local o `VITE_API_BASE` en el futuro). |
| Desarrollo backend | entorno Python local + `python app/run.py` | Necesita una PostgreSQL accesible vía `DATABASE_URL`. |

> Estado real del código: el cliente HTTP fija el prefijo `/api` (`frontend/src/api/client.ts`); la variable `VITE_API_BASE` definida en `docker-compose.yml` **no es consumida** por el código (reservada). Ver `desarrollo.md`.
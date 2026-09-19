# Desarrollo

## Entorno recomendado: Docker Compose

Levantar todo como en producción:

```bash
cp .env.example .env
docker compose up -d --build
```

Notas:

- El `entrypoint.sh` del backend aplica migraciones, seed y arranca uvicorn **sin `--reload`**. Para hot-reload del backend hay que sobrescribir el comando:

  ```bash
  docker compose exec backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

- Para hot-reload del frontend, correr Vite en el host (cambios se reflejan al instante mientras `docker compose up` mantenga la API y la base):

  ```bash
  docker compose up -d db backend
  cd frontend
  pnpm install
  pnpm dev        # servidor en: http://localhost:5173 (proxy /api → localhost:8000)
  ```

- El cliente fija el prefijo `/api` (`src/api/client.ts`); el proxy de Vite lo reescribe a `localhost:8000` (ver `vite.config.ts`).

## Entorno local sin Docker (opcional)

Backend: requiere Python 3.12 y una PostgreSQL alcanzable.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
$env:DATABASE_URL = "postgresql+psycopg://cobranzas:cobranzas@localhost:5432/cobranzas"
python -m app.run               # uvicorn en :8000
alembic upgrade head
python -m app.seed
```

> `python -m app.run` levanta uvicorn pero **no** ejecuta migraciones/seed (eso lo hace el entrypoint de Docker). En local se ejecutan a mano.

## Tests

La suite usa una base PostgreSQL separada **`cobranzas_test`**, que el `conftest.py` crea, migra y trunca automáticamente. Si PostgreSQL no está disponible, los tests dependientes se **omiten** (no fallan).

```bash
docker compose exec backend pytest -q            # dentro del contenedor (recomendado)
docker compose exec backend pytest tests/test_alertas.py -v   # un archivo
docker compose exec backend pytest -k escenario10 -v          # filtrar
```

Si se corre en el host, `conftest.py` toma `DATABASE_URL` del entorno y deriva la base de test de ahí.

### Cobertura actual (resumen)

- Autenticación y autorización (login, `/auth/me`, 401/403).
- Escenarios 8/9/10/13: unicidad por período, períodos distintos, cambio de tipo sin duplicar, aislamiento entre operadores.
- Cargas por operador: los 4 motivos, filas sin gestión, sin encabezado, motivo inválido, extensión inválida, `resumen`, y prohibición a operador.
- Reglas de alerta (test puro, sin BD).

## Cómo agregar un endpoint

1. **Caso de uso en `services/`** (lógica de aplicación), accediendo a datos vía `repositories/`.
2. **Router en `routers/`** (HTTP + permisos). Usar `require_supervisor` / `get_current_usuario` de `app/core/deps.py`.
3. **Schemas Pydantic** para entrada/salida; respuestas extendiendo `ORMModel` (valida `UUID → str`).
4. Registrar el router en `app/main.py`.
5. Añadir test en `tests/` (con `client`, `supervisor`, `operador` y helpers de `conftest.py`).

## Cómo agregar una columna/tabla

1. Modelo en `app/models/` (convenciones: `id` UUID, `Mapped`).
2. Migración:
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "nueva_columna"
   docker compose exec backend alembic upgrade head
   ```
3. **Revisar la migración generada**: en este proyecto los enums viven en la BD (`create_type=False`) y hay índices especiales (p. ej. único parcial de período vigente); ver `base-de-datos.md`.
4. Si el cambio afecta la API, actualizar schema y tests.

## Convenciones del código

- **Reglas de negocio en `domain/`** (sin dependencias de infraestructura). Ej.: `alertas.py`, `cargas.py`. No duplicarlas en routers ni en el frontend.
- Routers **delgados**: validan permisos y delegan en la capa de servicio.
- Servicios usan los repositorios; no construyen SQL crudo salvo excepción justificada. (Se detectaron algunas queries directas con `db.query(...)` en servicios — deuda menor, ver `auditoria-tecnica.md`.)
- Docstrings en módulos y funciones públicas (en línea con el código existente).
- Comentarios que explican el **porqué**, no el qué.
- `schemas` de salida usan `ORMModel` (UUID → `str`) para serialización consistente.
- Frontend: React Query para datos, tipos compartidos en `src/api/types.ts`, render de alertas únicamente desde lo que devuelve el backend.

## Verificaciones antes de publicar

```bash
docker compose exec backend pytest -q
docker compose build               # compila el frontend TS (consistencia de tipos)
alembic revision --autogenerate -m "verif" && git checkout alembic/versions   # drift-check de BD
```

- No dejar `console.log` de depuración (eliminarlos; ver `seguridad.md`).
- No versionar `.env`.
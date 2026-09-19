# Base de datos

## Resumen

- **Motor**: PostgreSQL 16 (`postgres:16-alpine`) dentro del contenedor `db`.
- **Base**: `cobranzas` (DB por defecto; seg. `POSTGRES_DB`). Host accesible en la red interna como `db:5432`.
- **Driver de aplicación**: `psycopg` v3 (URL `postgresql+psycopg://…`).
- **Migraciones**: Alembic. La única revisión actual es `0001_initial` (crea esquema, enums, tablas e índices). Se aplica automáticamente en el arranque del backend y manualmente con `alembic upgrade head`.
- El esquema completo (tablas, enums, relaciones) está en [modelo-datos.md](modelo-datos.md).

> La suite de tests crea una segunda base **`cobranzas_test`** en el mismo servidor y la migra/trunca por su cuenta. No debe modificarse a mano.

## Acceso

El puerto `5432` **no se publica al host**; se entra solo desde dentro de la red de Compose:

```bash
docker compose exec db psql -U cobranzas -d cobranzas
```

Para depurar puntualmente desde el host se puede publicar el puerto temporalmente (ver `configuracion.md`, red interna). Nunca en producción.

## Migraciones (Alembic)

```bash
docker compose exec backend alembic upgrade head      # aplicar pendientes
docker compose exec backend alembic current                    # en qué revisión está
docker compose exec backend alembic history                    # historial de revisiones
docker compose exec backend alembic downgrade 0001             # retroceder una revisión (no recomendado con datos)
docker compose exec backend alembic revision --autogenerate -m "nueva_migracion"   # generar
```

Flujo para agregar columnas/tablas:

1. Modificar los modelos en `backend/app/models/`.
2. Generar: `alembic revision --autogenerate -m "descripcion"`.
3. **Revisar** el archivo generado en `backend/alembic/versions/` (los `autogenerate` pueden perder índices parciales o enums; confirmar que respeta `create_type=False` y los `postgresql.ENUM` existentes).
4. Aplicar: `alembic upgrade head`.

Verificación de que el modelo coincide con la BD (sin aplicar): `alembic revision --autogenerate -m "verif"` e inspeccionar las diferencias que reporte.

### Restricciones del autogenerate, propias del proyecto

- Los enums se crean a nivel base de datos (`postgresql.ENUM`) y el ORM usa `create_type=False`; el autogenerate puede sugerir recrearlos. Mantener esa convención (ver `architectura.md` → "Columnas enum").
- Índices especiales (p. ej. el índice parcial `UNIQUE` de período vigente en `periodos`) deben verificarse a mano en la migración generada.

## Respaldos (backup) y restauración

La recomendación de operación es **`pg_dump` lógico** (compacto, restaurable) ejecutado desde el contenedor:

```bash
# Backup
docker compose exec -T db pg_dump -U cobranzas -d cobranzas --format=custom -f /tmp/cobranzas.dump
docker compose cp db:/tmp/cobranzas.dump ./cobranzas-$(date +%F).dump

# o SQL comprimido (más sencillo para inspeccionar)
docker compose exec -T db pg_dump -U cobranzas -d cobranzas | gzip > cobranzas-$(date +%F).sql.gz

# Restaurar (¡detiene la app y reemplaza la base!)
docker compose cp ./cobranzas-YYYY-MM-DD.dump db:/tmp/
docker compose exec db pg_restore -U cobranzas -d cobranzas --clean --if-exists /tmp/cobranzas-YYYY-MM-DD.dump
```

Para automatizar: crontab del host que copie el dump a un volumen/backup remoto (ver `mantenimiento.md`).

## Datos de desarrollo (seed)

`python -m app.seed` crea (solo si faltan):

- Catálogos: `PROMESA_PAGO`, `DEUDA_BONIFICADA`; motivos `PAGOS`, `DEUDAS_SIN_NC`.
- Usuarios: `supervisor`, `operador1`, `operador2` (credenciales en `instalacion.md`).
- Períodos: Agosto–Noviembre 2026 (Septiembre vigente).
- Clientes `100001–100008`, `200001–200002` y gestiones de ejemplo que cubren todas las combinaciones de alertas.

Es idempotente: si el registro existe, no lo duplica. Volver a ejecutarlo no corrige ni pisa datos cambiados a mano.

## Prácticas

- Nunca modificar tablas fuera de Alembic (rompe `current`/`history` y el drift-checking).
- Las filas de `gestiones` tienen unicidad `(cliente_id, periodo_id)`; no intentar forzar duplicados a mano.
- `conciliaciones` y `registros_conciliacion` están sin uso (módulo desactivado); conservarlas por si se reactivara.
- Para limpiar el entorno por completo: `docker compose down -v` **borra `pgdata`** (equivale a eliminar la base). Antes, backup.
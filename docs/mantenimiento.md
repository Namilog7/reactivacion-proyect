# Mantenimiento

## Rutinas de operación

| Tarea | Frecuencia | Comando / acción |
|-------|------------|------------------|
| Estado del stack | Diaria | `docker compose ps` |
| Revisión de logs | Diaria | `docker compose logs --tail=200 backend`; `docker compose logs --tail=200 frontend` |
| Healthcheck | Cada pocos minutos (o vía cron) | `curl -fsS http://localhost:8080/api/health` y alertar si falla |
| Backup de PostgreSQL | Diaria/semanal según política | `pg_dump` (ver `base-de-datos.md`) + copia fuera de la máquina |
| Verificación de backup | Semanal | Restaurar/inspeccionar el último dump (al menos `pg_restore --list`) |
| Uso de disco | Semanal | `docker system df` (+ `df -h` en la partición de volúmenes) |
| Actualización de imágenes base | Trimestral / cuando se requiera | Rebuild con `docker compose build --pull` y validación |

### Automatización sugerida del backup (crontab del host)

```bash
# /etc/crontab — 3:00 diario
0 3 * * * root   cd /opt/reactivacion-proyect && docker compose exec -T db pg_dump -U cobranzas -d cobranzas | gzip > /backups/cobranzas-$(date +\%F).sql.gz && find /backups -name '*.sql.gz' -mtime +30 -delete
```

> El host debe montar (o copiar) `/backups` a un destino remoto; el backup en la misma máquina no protege contra fallo de disco.

## Ciclo de vida del período de cobranzas

La aplicación no cierra períodos automáticamente:

1. El supervisor crea el período nuevo (`POST /periodos`) y lo marca como **vigente** al llegar la fecha.
2. A partir de ahí, las listas, el dashboard y las cargas por operador usan el período vigente.
3. Los períodos anteriores quedan como históricos (las gestiones no se borran).

No hay tarea de archivo: los datos permanecen en la base.

## Actualización de la aplicación

```bash
git pull
docker compose build            # reconstruye frontend (Node) y backend (Python)
docker compose up -d
docker compose logs backend     # esperar "alembic upgrade head" + "[seed] OK"
```

- Las migraciones se aplican automáticamente (`entrypoint.sh`). Antes de actualizar a una versión con migración nueva, hacer backup.
- Si una migración falla, ver `troubleshooting.md` ("migración").

## Cambio de credenciales / secretos

- Rotar `SECRET_KEY`: actualizar `.env` y reiniciar backend. **Invalida todos los tokens activos.** Programar la rotación en horario de baja actividad.
- Cambiar `POSTGRES_PASSWORD`: actualizar `.env` (los tres valores: `POSTGRES_PASSWORD`, `DATABASE_URL`) y recrear el contenedor `db` **y** el `backend` (este último reconecta leyendo la URL nueva):

  ```bash
  docker compose up -d --force-recreate db backend
  ```

## Monitoreo actual

El sistema ofrece:

- `GET /health` → `{"status":"ok"}` (disponible también vía `/api/health`).
- Logs estructurados de uvicorn/Nginx en las consolas de los contenedores.
- Healthcheck de PostgreSQL (`pg_isready`) visible en `docker compose ps` (columna STATUS `(healthy)`).

No hay métricas (Prometheus), alertas ni *tracing* integrados. Para producción se recomienda al menos: chequeo externo del `/api/health` y alerta de disco (ver `auditoria-tecnica.md`).

## Riesgos operativos conocidos

- `docker compose down -v` **borra la base** (volumen `pgdata`). Restringir su uso en producción.
- No hay política automática de retención de archivos/backups más allá del ejemplo de crontab.
- Los volúmenes `pgdata` y `uploads_data` residen en el host; respaldar también su partición si se descarta `pg_dump`.
- El módulo de conciliación está desactivado; las tablas correspondientes siguen en la base (no requieren mantenimiento, pero deben tenerse en cuenta al hacer `TRUNCATE`/limpiezas masivas, p. ej. en tests).
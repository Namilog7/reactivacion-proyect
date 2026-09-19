# Instalación (guía rápida)

> Para el procedimiento completo orientado a infraestructura, ve `manual-instalacion.md`.

## Requisitos

- Docker Engine **20.10+** con el plugin Docker Compose v2.
- 2 GB de RAM libres (PostgreSQL 16 + uvicorn + Nginx son livianos).
- Puerto `8080` libre en el host (configurable con `FRONTEND_PORT`).
- No hace falta instalar Python ni Node en el host: todo se compila dentro de los contenedores.

## Pasos

1. **Preparar el entorno**

   ```bash
   cp .env.example .env
   ```

   Como mínimo, en `.env`, cambia `POSTGRES_PASSWORD` y `SECRET_KEY` (instrucciones en `configuracion.md`).

2. **Levantar la aplicación**

   ```bash
   docker compose up -d --build
   ```

   El primer build puede tardar varios minutos (instala dependencias de Python y compila el frontend con Vite).

3. **Verificar**

   ```bash
   docker compose ps
   # NAME            STATUS
   # ...db           (healthy)
   # ...backend      Up
   # ...frontend     Up

   curl http://localhost:8080/api/health        # {"status":"ok",...}
   docker compose logs backend | tail           # "[seed] OK"
   ```

4. **Entrar**

   - Frontend: <http://localhost:8080>
   - Swagger/OpenAPI: <http://localhost:8080/api/docs>
   - Login con un usuario de seed (ver README).

> Si la API está alojada en otro host (modo externo, configuración actual del repo),
> el frontend la alcanza vía `frontend/nginx.conf` sin pasos adicionales. Si vas a
> desplegar todo en esta máquina, ajusta `nginx.conf` como indica `despliegue.md`.

## Operación diaria

```bash
docker compose ps                # estado
docker compose logs -f backend   # en vivo
docker compose down              # detener (conserva datos en volúmenes)
docker compose up -d             # volver a levantar
```

## Actualización

```bash
git pull
docker compose build
docker compose up -d
```

Las migraciones se aplican solas al arrancar el backend (`alembic upgrade head`).

## Reinicio en frío / recuperación

La base y los datos persisten en los volúmenes `pgdata` y `uploads_data`:

```bash
docker compose down        # detiene pero NO borra datos
docker compose up -d       # reutiliza los volúmenes
```

> `docker compose down -v` **borra los volúmenes** (equivalente a un formateo). Usarlo solo si se quiere recrear todo desde cero. Backups: `base-de-datos.md`. Solución de problemas: `troubleshooting.md`.

## Datos de desarrollo (seed)

El backend ejecuta `python -m app.seed` en cada arranque. Es **idempotente**: crea catálogos, usuarios, períodos (Agosto-Noviembre 2026, con Septiembre vigente), clientes y gestiones de ejemplo que ejercitan todas las combinaciones de alertas. No borra ni pisa datos existentes.

Usuarios iniciales: `supervisor / supervisor123`, `operador1 / operador123`, `operador2 / operador123`.
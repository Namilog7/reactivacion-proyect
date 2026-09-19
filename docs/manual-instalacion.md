# Manual de instalación (entorno de producción)

Procedimiento paso a paso para dejar el sistema funcionando en un servidor de la empresa, apto para ser ejecutado por personal de infraestructura. Para la guía rápida `cp .env.example .env && docker compose up -d --build`, ver `instalacion.md`; para despliegue en Render, ver `despliegue.md`.

**Tiempo estimado**: 30-60 minutos + validación.

---

## Paso 1 — Requisitos del servidor

| Recurso | Valor recomendado |
|---------|-------------------|
| SO | Linux (Ubuntu 22.04 LTS o similar) con acceso root/sudo |
| CPU / RAM | 2 vCPU / 2 GB mínimo (PostgreSQL 16 + uvicorn + Nginx) |
| Disco | 20 GB+ (volúmenes Docker + backups) |
| Docker | Docker Engine 20.10+ **con** plugin `docker compose` (v2) |
| Red | Puerto `8080` (o el configurado) accesible internamente; `443` abierto si hay DNS público |

El equipo no necesita Python ni Node: todo se compila en los contenedores.

## Paso 2 — Instalar Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# cerrar y abrir sesión (o: newgrp docker)
docker --version
docker compose version          # debe aparecer "v2.x"
```

## Paso 3 — Obtener el código

```bash
sudo mkdir -p /opt/reactivacion-proyect
cd /opt/reactivacion-proyect
# clonar el repositorio provisto por el equipo de desarrollo
git clone <URL_DEL_REPOSITORIO> .
```

## Paso 4 — Configurar el entorno

```bash
cp .env.example .env
vi .env
```

Valores a completar (ver `configuracion.md`): `POSTGRES_PASSWORD`, `DATABASE_URL` (misma contraseña), `SECRET_KEY`, `FRONTEND_PORT`. Generar secretos:

```bash
openssl rand -base64 48          # SECRET_KEY
openssl rand -base64 16          # contraseña PostgreSQL
```

## Paso 5 — Decidir el modo de conexión API

- **Modo local (recomendado)**: el backend corre en la misma máquina. Editar `frontend/nginx.conf` reemplazando el bloque `location /api/` por:

  ```nginx
  location /api/ {
      proxy_pass http://backend:8000/;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_http_version 1.1;
      proxy_buffering off;
  }
  ```

  (eliminar `proxy_ssl_server_name`/`proxy_ssl_name`/`Host` manual y el `proxy_pass https://…`).

- **Modo externo**: la API está en otro host (ej. Render). Dejar `frontend/nginx.conf` como viene: requiere SNI (`proxy_ssl_server_name on`) y `Host` correcto; si el backend cambia de URL, actualizar `proxy_pass`/`proxy_ssl_name`/`Host` y **recompilar** el frontend.

## Paso 6 — Construir y levantar

```bash
docker compose up -d --build
```

Primer build: varios minutos (instala Python deps y compila el frontend).

## Paso 7 — Verificar

```bash
docker compose ps                 # db (healthy), backend/frontend Up
curl -fsS http://localhost:8080/api/health        # {"status":"ok"}
curl -I http://localhost:8080/                    # 200
curl -fsS http://localhost:8080/api/docs | head   # Swagger presente
docker compose logs backend | tail               # "[seed] OK"
```

Abrir `http://localhost:8080`, loguear con `supervisor`/`supervisor123` (seed).

## Paso 8 — DNS y HTTPS

La app debe servirse **siempre por HTTPS** en producción:

1. Registrar un registro **A** de `app.empresa.com` → IP del servidor.
2. Terminar TLS con un reverse proxy del host (Caddy, o Nginx/certbot), enrutando a `http://127.0.0.1:8080` (el puerto del frontend en el host).
3. Redirigir HTTP → HTTPS (el proxy lo hace con la config por defecto de Caddy).

Ejemplo mínimo con Caddy:

```
app.empresa.com {
    reverse_proxy 127.0.0.1:8080
}
```

> No exponer el backend ni PostgreSQL hacia Internet (ver `seguridad.md`).

## Paso 9 — Backups automáticos

Instalar el cron del host (ajustar ruta al repo):

```bash
crontab -e
# 3:00 diario — respaldo comprimido + retención 30 días
0 3 * * *   cd /opt/reactivacion-proyect && docker compose exec -T db pg_dump -U cobranzas -d cobranzas | gzip > /backups/cobranzas-$(date +\%F).sql.gz && find /backups -name '*.sql.gz' -mtime +30 -delete
```

**Copiar `/backups` a otro medio** (otra máquina/volumen externo). Ver `base-de-datos.md` y `mantenimiento.md`.

## Paso 10 — Monitoreo básico

- Chequeo externo cada 5 min: `curl -fsS http://127.0.0.1/api/health` y alerta vía correo/Slack del equipo.
- Revisión de disco: `df -h` y `docker system df`.
- Con acceso a la app, revisar diariamente el dashboard del supervisor.

## Paso 11 — Usuarios reales

1. El supervisor crea los usuarios del equipo (menú Usuarios) con rol correcto.
2. **Cambiar la contraseña** de los tres usuarios de seed y, si no se necesitan, **desactivarlos** (la app soporta `activo=false`).
3. Guardar credenciales en el gestor de contraseñas de la empresa.

## Paso 12 — Actualización del sistema

```bash
cd /opt/reactivacion-proyect
git pull
docker compose build
docker compose up -d
docker compose logs backend     # esperar migraciones + "[seed] OK"
```

Antes de actualizar a una versión con migraciones nuevas: **backup** (paso 9).

## Paso 13 — Recuperación ante desastres

1. Levantar un servidor nuevo con Docker (pasos 1-2).
2. Instalar el código con la **misma** versión del backup (paso 3, checkout de la versión).
3. Copiar el `.env` (mismos secretos) y `nginx.conf` (pasos 4-5).
4. `docker compose up -d --build`.
5. Restaurar la base desde el último dump (comandos en `base-de-datos.md`).

Tiempo objetivo con automatización del backup: < 2 h.

## Paso 14 — Checklist de seguridad

- [ ] `SECRET_KEY` aleatoria y única en el servidor.
- [ ] `POSTGRES_PASSWORD` fuerte; `DATABASE_URL` coincidente.
- [ ] Usuarios seed desactivados o con password cambiada.
- [ ] HTTPS activo y redirigiendo HTTP.
- [ ] Backend y PostgreSQL no expuestos al host.
- [ ] Backups automáticos probados.
- [ ] `console.log` de depuración ausentes del build (ver `seguridad.md`/`auditoria-tecnica.md`).

## Paso 15 — Prueba funcional de aceptación (UAT)

- [ ] Login operador y supervisor con usuarios reales.
- [ ] Dashboard operador muestra sus gestiones del período vigente.
- [ ] Crear una gestión; verificar historial al editarla.
- [ ] Intentar crear una gestión duplicada (cliente+período) → debe rechazarse.
- [ ] Supervisor: subir un `.xlsx` de 2-3 clientes con un motivo → verificar los flags en las gestiones.
- [ ] Revisar las alertas (reglas 1-4) en el listado.

## Paso 16 — Documentación y entrega

- Registrar en el gestor de la empresa: URL, usuarios creados, política de contraseñas, dueño del sistema, cron de backups.
- Guardar la salida de `docker compose config` como referencia de la configuración efectiva.
- Entregar este manual junto con `configuracion.md`, `mantenimiento.md` y `auditoria-tecnica.md`.
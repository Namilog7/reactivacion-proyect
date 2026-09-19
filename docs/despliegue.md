# Despliegue

Se documentan dos topologías soportadas por el código actual.

## Topología A — Todo en una máquina (recomendada para producción)

El frontend, el backend y la base corren juntos con Compose en la misma red interna.

```
Internet
   │ HTTPS :443
   ▼
Reverse proxy del host (Caddy / Nginx host / Traefik + certbot)
   │ HTTP :80 (o interno) → frontend container
   ▼
frontend (nginx :80)   ├── estático React
                       └── /api → proxy_pass http://backend:8000/ (locally)
backend  (uvicorn :8000)  → PostgreSQL 16
db       (PostgreSQL :5432, sin puerto en el host)
```

### Pasos

1. Preparar la máquina (Docker + Compose, 2 vCPU / 2 GB) — detalle en `manual-instalacion.md`.
2. `cp .env.example .env` y completar secretos (`configuracion.md`).
3. **Ajustar el proxy API a modo local** en `frontend/nginx.conf`:

   ```nginx
   location /api/ {
       proxy_pass http://backend:8000/;     # slash final: quita /api
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_http_version 1.1;
       proxy_buffering off;
   }
   ```

   Elimina las líneas `proxy_pass https://reactivacion-backend.onrender.com/`, `proxy_ssl_server_name`, `proxy_ssl_name` y el `Host` manual.

4. `docker compose up -d --build`.
5. TLS sobre el puerto `80` del contenedor con un reverse proxy del host (El tráfico `8080→80` no es seguro por sí mismo).
6. Backups automáticos y monitoreo (`mantenimiento.md`).

## Topología B — Backend externo (configuración actual del repo)

El frontend corre donde tú quieras y la API vive en otra infraestructura (hoy: Render en `https://reactivacion-backend.onrender.com`). El Nginx del frontend hace proxy HTTPS hacia ese host.

```
Browser → frontend (nginx :80)
            /api → proxy_pass https://reactivacion-backend.onrender.com/   (HTTPS)
                        │  Host + SNI obligatorios
                        ▼
              Cloudflare → Render (FastAPI)
```

### Requisito SNI (clave)

Cuando el upstream es **HTTPS con host virtual** (Cloudflare/Render), Nginx debe enviar el **Server Name Indication** y el encabezado `Host` correctos. El default de Nginx es `proxy_ssl_server_name off`, lo que produce:

```
SSL_do_handshake() failed (SSL: error:14094410:SSL routines:... handshake failure)
... upstream server temporarily disabled while SSL handshaking to upstream ...
→ 502 Bad Gateway (login y todos los /api/*)
```

La configuración correcta (aplicada en el repo):

```nginx
proxy_pass https://reactivacion-backend.onrender.com/;
proxy_ssl_server_name on;
proxy_ssl_name reactivacion-backend.onrender.com;
proxy_set_header Host reactivacion-backend.onrender.com;
```

Referencia del caso real y la verificación: `troubleshooting.md`.

### Consideraciones

- El `Host` y el destino están **fijos en el código** (`frontend/nginx.conf`). Para otra instancia de backend externo hay que recompilar el contenedor.
- Toda la información circula por Internet hacia el proveedor: evaluar implicaciones de privacidad de datos (ver `seguridad.md`).

## Comparación de topologías

| Criterio | A (todo local) | B (backend externo) |
|----------|----------------|----------------------|
| Ubicación de los datos | En la empresa | En el proveedor externo |
| Dependencia de terceros | Ninguna | Render/Cloudflare |
| Complejidad | Baja (mismo stack) | Requiere SNI + DNS y cableado del upstream |
| Mantenimiento | Un solo stack | Dos lugares distintos |
| Recomendación | **Producción** | Demo / desarrollo remoto |

## Varillas de seguridad para cualquier despliegue

- Terminar HTTPS siempre (nunca servir credenciales por HTTP plano).
- No exponer puertos de backend ni de PostgreSQL al host.
- Secretos por variables de entorno / gestor de secretos, nunca en el repositorio ni en imágenes.
- Política de contraseñas y desactivación de usuarios inactivos en la app.
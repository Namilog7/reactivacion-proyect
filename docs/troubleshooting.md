# Solución de problemas

## Índices rápidos

| Síntoma | Causa probable → solución |
|---------|---------------------------|
| `502 Bad Gateway` en `/api/*` | Proxy HTTPS sin SNI (caso backend externo) → abajo, **sección 1** |
| `502` en modo local | Backend caído o no responde en `backend:8000` → **sección 2** |
| `404` en `/api/*` | Trailing slash del `proxy_pass` o backend montando rutas distintas → **sección 3** |
| Login rechazado siempre | Token inválido/vencido, usuario inactivo, o reloj del host mal → **sección 4** |
| `409` al crear gestión | Cliente ya tiene gestión en ese período (comportamiento esperado) → **sección 5** |
| Carga devuelve `400` | Sin período vigente, motivo inválido o extensión no `.xlsx` → **sección 6** |
| Swagger no abre | Ruta incorrecta → `http://<host>:8080/api/docs` |
| Contenedores no levantan | Puerto en uso o red Docker → **sección 7** |
| `alembic` falla al arrancar | Migración pendiente o BD corrupta → **sección 8** |

---

## 1. 502 en `/api/*` con backend externo (el caso real del proyecto)

Antes: todos los `/api/*` (login incluido) devolvían `502`. Logs de Nginx:

```
SSL_do_handshake() failed (SSL: error:14094410:SSL routines:SSL3_READ_BYTES:sslv3 alert handshake failure)
... peer closed connection in SSL handshake while reading from upstream
"upstream server temporarily disabled while SSL handshaking to upstream"
```

Y del lado del destino (o probando `https://reactivacion-backend.onrender.com`): el upstream queda detrás de Cloudflare/Render (`216.24.57.16/.18`, `*.origin.onrender.com.cdn.cloudflare.net`), que rechaza handshakes **sin SNI**.

**Confirmación** (una sola prueba basta):

```bash
# Python: sin SNI → falla el handshake
python -c "import socket,ssl; ctx=ssl.create_default_context(); s=socket.socket(); ctx.wrap_socket(s).connect(('216.24.57.16',443))"
# → SSLV3_ALERT_HANDSHAKE_FAILURE (o similar)

# Con SNI → OK
python -c "import urllib.request as u; print(u.urlopen('https://reactivacion-backend.onrender.com/health').status)"
# → 200
```

**Verificar el Nginx corriendo** (debe existir `proxy_ssl_server_name`):

```bash
docker compose exec frontend nginx -T | Select-String "proxy_pass|proxy_ssl_server_name|proxy_ssl_name"   # PowerShell
```

**Solución** (aplicada en `frontend/nginx.conf`; requiere build/restart para que el contenedor la tome):

```nginx
proxy_pass https://reactivacion-backend.onrender.com/;
proxy_ssl_server_name on;
proxy_ssl_name reactivacion-backend.onrender.com;
proxy_set_header Host reactivacion-backend.onrender.com;
```

Tras editar: `docker compose up -d --build frontend` y probar `curl http://localhost:8080/api/health`.

## 2. 502/504 en modo local (`proxy_pass http://backend:8000/`)

- ¿Está el backend arriba? `docker compose ps`; `docker compose logs backend`.
- ¿Responde? `docker compose exec frontend wget -qO- http://backend:8000/health`.
- ¿La BD está sana? STATUS de `db` debe decir `(healthy)`. Si `db` no está, el backend no puede arrancar (`entrypoint` → `alembic` falla).

## 3. 404 en `/api/*` — importa el `proxy_pass` (con o sin slash)

- `proxy_pass http://backend:8000;` (sin `/`) → reenvía `/api/auth/login` tal cual → el backend responde **404**.
- `proxy_pass http://backend:8000/;` (con `/`) → con `location /api/`, el prefijo se **quita** (`/auth/login`). Correcto.
- La clave es el trailing slash **dentro del bloque `location /api/`**. Mismo criterio aplica en el modo externo.

Puede dar 404 también si el backend no monta la ruta esperada: ver `docs/api.md` y Swagger (`/api/docs`).

## 4. Login negativo / sesión inválida

Causas y comprobaciones:

- **Credenciales erróneas**: respuesta `401`. El seed usa `supervisor / supervisor123`; `operador1` y `operador2 / operador123`.
- **Usuario inactivo**: `get_current_usuario` rechaza `activo=False`. Revisar en la app o `SELECT * FROM usuarios;`.
- **Token vencido**: expiración `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480). Volver a loguear.
- **Reloj del host desviado**: el JWT valida `exp` contra hora UTC. Si el host tiene fecha mal, las validaciones de expiración fallan. Sincronizar NTP y reiniciar backend.
- **Se rotó `SECRET_KEY`**: todos los tokens previos son inválidos (esperado).

Si hay un proxy extra (WAF, reverse proxy), verificar que no esté reescribiendo el encabezado `Authorization`.

## 5. `409 Conflict` al crear/`PATCH` una gestión

- Crear una gestión para un cliente que ya tiene una en el **mismo período** → `409` (unicidad de diseño, escenario 8 del requerimiento).
- Cambiar de tipo/operador en el mismo período no duplica: se actualiza la existente (escenario 10).

## 6. `400` en `POST /cargas`

| Detalle | Causa → acción |
|---------|----------------|
| `Debe seleccionar un archivo.` | Campo `file` ausente o filename vacío |
| `El archivo debe tener extensión .xlsx.` | Solo `.xlsx` (validación por extensión) |
| Sin período vigente | Crear un período y marcarlo `periodo_vigente=true` (supervisor) |
| Motivo no reconocido | Usar uno de `PAGO_DESBLOQUEO`, `PAGO_SIN_DESBLOQUEO`, `DEUDA_SIN_NC`, `DEUDA_SIN_NC_SIN_DESBLOQUEO` (catálogo: `GET /cargas/motivos`) |
| Parse error del XLSX | El archivo debe contener números de cliente (col 1) — ver `docs/cargas.md` |

Para ver el `detail` exacto de la respuesta, mirar `docker compose logs backend`.

## 7. Contenedores no levantan / puerto en uso

```bash
docker compose ps              # estado
docker compose logs frontend   # error de bind, build fallido, etc.
docker compose logs backend
```

- Puerto `8080` ocupado → cambiar `FRONTEND_PORT` en `.env` y hacer `docker compose up -d frontend` (recrea el mapeo).
- Memoria límite → `docker system df`, `docker info`.
- Build roto → revisar la salida de `docker compose build`.

## 8. Migraciones (Alembic)

- **Falló `alembic upgrade head` al arrancar**: `docker compose logs backend` mostrará la revisión y el error SQL. Diagnóstico típico: base no creada o un cambio manual fuera de migraciones.
  - Si la base no existe: `docker compose exec db psql -U cobranzas -d postgres -c "CREATE DATABASE cobranzas;"`.
- **Drift (modelo ≠ BD)**: `alembic revision --autogenerate -m "verif"` reportará diferencias. Inspeccionar y, si procede, generar la migración real (ver `base-de-datos.md`).
- **Revisión `head` pero tablas faltantes**: revisar si `versions/0001_initial.py` ejecutó todo y si los enums existen (`\dT` en psql).

## 9. Querés reiniciar todo desde cero

```bash
docker compose down -v     # BORRA datos (volúmenes). Solo desde cero.
docker compose up -d --build
```

El seed vuelve a crear catálogos, usuarios, períodos y gestiones de ejemplo. Para conservar datos pero re-ejecutar el seed: `docker compose exec backend python -m app.seed`.

## 10. Frontend roto (pantalla en blanco / error JS)

- Build limpio: `docker compose build frontend` y `docker compose up -d frontend`.
- Consola del navegador (F12) y `docker compose logs frontend`.
- Si se usa `pnpm dev`, verificar el proxy Vite y que el backend responde en `localhost:8000`.
- El token vive en `localStorage` (`cobranzas_token`); tras cambios de rol/permisos conviene hacer logout o `localStorage.clear()` en la consola y volver a loguear.
# Seguridad

Análisis de los controles implementados, de las limitaciones detectadas y de las recomendaciones. Documento de referencia: `auditoria-tecnica.md` (con prioridades).

## Controles implementados

| Control | Ubicación | Detalle |
|---------|-----------|---------|
| Hash de contraseñas | `app/core/security.py` | `bcrypt` (cost por defecto de la librería; 4.2.x) |
| JWT firmado | `app/core/security.py` | `HS256` con `SECRET_KEY`; claim `exp` = ahora + `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Validación de token por request | `app/core/deps.py` | `get_current_usuario`: valida firma/expiración y que el usuario exista y esté `activo` |
| Roles | `app/core/deps.py` | `require_supervisor` → `403` si no es SUPERVISOR |
| Aislamiento por dueño | `services`/`routers` de gestión | Un OPERADOR solo lee/edita sus gestiones; el SUPERVISOR ve todas |
| Unicidad de gestiones | modelo + servicio | `(cliente_id, periodo_id)` único → `409` en duplicados |
| Historial auditable | `models/historial.py` | `historial_cambios`: campo, valores anterior/nuevo (JSONB), usuario y origen del cambio |
| Desactivación lógica de usuarios | `usuarios` | `DELETE` inactiva (ya no puede autenticarse) |
| Validación de entrada | `schemas/` (Pydantic v2) | Tipos, longitud mínima de password, valores por defecto |
| Sin almacenamiento de archivos | `carga_service` | La carga procesa el `.xlsx` en memoria (menos superficie de ataque) |

## Controles de la infraestructura

- PostgreSQL y backend **no expuestos al host** (red interna de Compose).
- `frontend/nginx.conf`: `client_max_body_size 20m` (limita el tamaño de subidas).
- Extensión de archivo validada en la API (solo `.xlsx`) antes de parsear con `openpyxl`.
- El Nginx del frontend no sirve `.env` ni archivos del backend (solo `dist/` del build y proxy `/api`).
- Imágenes minimizadas (`python:3.12-slim`, `node:20-alpine` para build, `nginx:1.27-alpine`).

> **Deuda detectada**: los contenedores corren como `root` (los `Dockerfile` no definen usuario no-root).
> A corto plazo mitigar con el resto del hardening; a mediano plazo agregar `USER` en las imágenes.

## Hallazgos y limitaciones detectadas

### 1. `SECRET_KEY` por defecto (crítico en producción)

`app/config.py` define `clave-insegura-solo-para-desarrollo`. Si se despliega sin `.env`, **cualquier persona que conozca el código puede falsificar JWT**. Mitigación: inyectar `SECRET_KEY` aleatoria (ver `configuracion.md`). Si Rotar: los tokens viejos quedan inválidos.

### 2. CORS abierto

`app/main.py` configura `CORSMiddleware` con `allow_origins=["*"]` **y** `allow_credentials=True`. Combinación que los navegadores tratan de forma especial y que en la práctica equivale a "aceptar cualquier origen". Si toda la app se sirve por el mismo origen (recomendado), no aporta nada útil. **Recomendación**: restringir a los orígenes reales o eliminar el middleware en producción.

### 3. Token en `localStorage`

El JWT se guarda en `localStorage` (`key "cobranzas_token"`). Es accesible desde cualquier script que corra en ese origen (riesgo XSS). Alternativa estándar: cookie `HttpOnly` + `Secure` + `SameSite` y CSRF, o tokens de corta vida con refresh en cookie. Ver `auditoria-tecnica.md` (deuda).

### 4. Depuración residual en el cliente

`frontend/src/auth/AuthContext.tsx` imprime el token con `console.log` (líneas ~50-55). **Eliminar antes de producción** (ver `auditoria-tecnica.md`).

### 5. Sin rate-limiting en `/auth/login`

Un endpoint público sin límite de intentos permite fuerza bruta si las contraseñas son débiles y no hay mecanismo externo de mitigación (WAF/baseline en el reverse proxy).

### 6. Subida de archivos

- Validación por **extensión** (`.xlsx`), no por contenido (MIME). El contenido se valida al parsear con `openpyxl`; un archivo inválido devuelve `400`. Mantener `client_max_body_size` acotado (ya está en `20m`).
- La carga por operador no persiste el archivo (reduce riesgo); si se reactiva el módulo de conciliación, que sí lo escribía en `UPLOAD_DIR`, revisar esa ruta y la persistencia.

### 7. `VITE_API_BASE` sin uso

`docker-compose.yml` define `VITE_API_BASE: /api` pero el cliente fija el prefijo a mano (`frontend/src/api/client.ts`). No es un riesgo de seguridad sino de consistencia de configuración.

## TLS / terminación de HTTPS

- **Entorno actual**: el frontend se sirve por HTTP y el Nginx proxya por HTTPS a un backend externo. Para ese salto es **obligatorio** el SNI (`proxy_ssl_server_name on`) y `Host` correcto; sin ellos hay `handshake_failure` → 502 (caso real documentado en `troubleshooting.md`).
- **Producción**: terminar TLS en el reverse proxy del host (certificados Let's Encrypt / corporativo). Nunca servir credenciales por HTTP plano. Deshabilitar el acceso por HTTP si es posible (o redirigir a HTTPS).

## Recomendaciones priorizadas

Alta:

1. `SECRET_KEY` y contraseña de BD aleatorias en todo entorno desplegado.
2. Quitar los `console.log` con el token.
3. Restringir CORS a orígenes reales (o quitar el middleware en el esquema same-origin).
4. Backups automáticos de la base. HTTPS en producción.

Media:

5. Rate-limiting (o mitigación en el reverse proxy) sobre `/auth/login`.
6. Mover el token a cookie `HttpOnly`/`Secure` (con su estrategia CSRF) o tokens de corta vida.
7. Validación de tipo de contenido real del XLSX (MIME + firma) y límite de filas.
8. Centralizar secretos en un gestor (env/per-déployment platform secrets).

Baja:

9. Consumir `VITE_API_BASE` o eliminarla de Compose.
10. Policy de contraseñas más estricta (longitud mínima configurable, rotación) y auditoría de inicios de sesión fallidos.
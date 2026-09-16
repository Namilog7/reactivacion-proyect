# API

Todas las rutas del backend están montadas en la raíz y expuestas tras el prefijo `/api` por Nginx. Documentación interactiva: http://localhost:8080/api/docs

Autenticación: `Authorization: Bearer <token>` (JWT). Roles: `SUPERVISOR`, `OPERADOR`.

## Auth

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| POST | `/auth/login` | `{username, password}` → `{access_token, token_type, usuario}` | público |
| GET | `/auth/me` | Usuario autenticado | cualquier |

## Usuarios

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/usuarios` | Lista de usuarios | SUPERVISOR |
| POST | `/usuarios` | Crea usuario | SUPERVISOR |
| GET | `/usuarios/{id}` | Detalle | SUPERVISOR |
| PATCH | `/usuarios/{id}` | Actualiza (nombre, rol, activo, contraseña) | SUPERVISOR |
| DELETE | `/usuarios/{id}` | Inactiva usuario | SUPERVISOR |

## Períodos y catálogos

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/periodos` | Lista de períodos | cualquier |
| GET | `/periodos/vigente` | Período vigente (o null) | cualquier |
| POST | `/periodos` | Crea período | SUPERVISOR |
| PATCH | `/periodos/{id}` | Actualiza (incluye `periodo_vigente`) | SUPERVISOR |
| GET | `/tipos-operacion` | Catálogo de tipos | cualquier |
| GET | `/motivos-conciliacion` | Catálogo de motivos (reservado) | cualquier |

## Gestiones

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/gestiones` | Lista paginada y filtros (`periodo_id`, `operador_id`, `q`, `tipo_operacion_id`, `pago`, `desbloqueado`, `tiene_nc`, `alerta=SI\|CRITICA`, `sort`, `order`, `page`, `page_size`) | propio operador / todos (supervisor) |
| POST | `/gestiones` | Crea gestión. El supervisor **debe** indicar `operador_id`. `409` si el cliente ya tiene gestión en el período. | operador/supervisor |
| GET | `/gestiones/{id}` | Detalle con alertas | dueño/supervisor |
| PATCH | `/gestiones/{id}` | Actualiza campos; registra historial | dueño/supervisor |
| GET | `/gestiones/{id}/historial` | Historial de cambios (campo, origen, valores, usuario) | dueño/supervisor |

Una gestión devuelve `alertas` (nivel, flags por celda y mensajes) evaluadas por el backend.

## Cargas por operador

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/cargas/motivos` | Motivos disponibles para cargar (`PAGO_DESBLOQUEO`, `PAGO_SIN_DESBLOQUEO`, `DEUDA_SIN_NC`, `DEUDA_SIN_NC_SIN_DESBLOQUEO`) | SUPERVISOR |
| GET | `/cargas/resumen` | Estado por operador en el período vigente (gestiones, pagos, alertas) | SUPERVISOR |
| POST | `/cargas` | Sube XLSX (`multipart/form-data`: `file`, `operador_id`, `motivo`, opcional `periodo_id`) y actualiza las gestiones del operador según el motivo | SUPERVISOR |

La carga solo actualiza las gestiones existentes de ese operador en el período (vigente por defecto); las filas sin gestión se ignoran y se informan en la respuesta (`sin_gestion`). No persiste auditoría.

## Dashboard

| Método | Ruta | Descripción | Acceso |
|--------|------|-------------|--------|
| GET | `/dashboard/operador` | Métricas + gestiones del operador | OPERADOR |
| GET | `/dashboard/supervisor` | Resumen global (por período, ocupación de operadores, alertas) | SUPERVISOR |

## Health

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
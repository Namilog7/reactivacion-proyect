# Auditoría técnica

**Fecha**: 2026-09-19 · **Alcance**: repositorio completo (`backend/`, `frontend/`, `docker-compose.yml`, infraestructura asociada). **Método**: revisión estática del código + ejecución de la suite de tests + diagnóstico real del fallo de conectividad (`502`, SNI).

---

## Resumen ejecutivo

El sistema está bien estructurado: capas del backend desacopladas, reglas de negocio centralizadas en `app/domain/`, control de acceso por rol y por dueño cubierto por tests, y despliegue contenedorizado simple. La **deuda más importante es de configuración/hardening** (secretos por defecto, CORS abierto, token en `localStorage`, depuración residual), no de diseño. También hay que decidir la **topología de despliegue** para la empresa: la configuración actual del repo apunta la API a un backend externo (Render), lo que significa que los datos salen de la infraestructura propia si se despliega tal cual.

---

## 1. Fortalezas

| Área | Detalle |
|------|---------|
| **Arquitectura por capas** | `domain/` (reglas puras), `models/`, `repositories/`, `services/`, `routers/` delgados, `schemas/` Pydantic v2 con serialización `UUID→str` centralizada (`ORMModel`). |
| **Regla de negocio en un solo lugar** | Evaluación de alertas (reglas 1-4) y motivos de carga viven en `domain/alertas.py` y `domain/cargas.py`; el frontend solo renderiza lo que devuelve el backend. Evita duplicación y deriva de comportamiento. |
| **Seguridad de acceso** | Roles (SUPERVISOR/OPERADOR) + aislamiento por dueño (operador solo accede a sus gestiones) cubiertos por tests (escenarios 8/9/10/13). |
| **Integridad de datos** | Unicidad `(cliente_id, periodo_id)` en `gestiones`; único período vigente con índice parcial; enums a nivel de base. |
| **Auditoría** | `historial_cambios` con campo, valores anterior/nuevo en JSONB, usuario y origen del cambio. |
| **Ciclo de vida del dato** | Migraciones Alembic + seed idempotente ejecutados automáticamente al arrancar el contenedor (`scripts/entrypoint.sh`). Facilita mucho el deploy. |
| **Pruebas** | Suite pytest con base Postgres **separada** (`cobranzas_test`), que se omite si la BD no está disponible (no rompe el pipeline en entornos livianos). Cubre auth, escenarios clave, carga por operador y alertas. |
| **Containerización** | Red interna de Compose sin exponer backend ni Postgres al host; healthcheck real de Postgres (`pg_isready` y condición `service_healthy`); volúmenes con nombre para datos. |
| **Frontend** | TypeScript, React Query para datos, badgets de alerta accesibles (`aria-label`/`title` en `components/ui.tsx`). |
| **Operatividad del diagnóstico** | El incidente de `502` se resolvió con evidencia reproducible (handshake SSL sin SNI vs con SNI), y la solución quedó aplicada y documentada. |

---

## 2. Riesgos

| # | Riesgo | Severidad | Descripción / evidencia |
|---|--------|-----------|--------------------------|
| R1 | **`SECRET_KEY` por defecto** | **ALTA** | `app/config.py:10` define `clave-insegura-solo-para-desarrollo`; Compose la usa si no se inyecta `.env`. Quien conozca el código podría forjar JWT válidos. |
| R2 | **Datos hacia un proveedor externo por defecto** | **ALTA** (según política de datos) | `frontend/nginx.conf` proxya `/api` a `https://reactivacion-backend.onrender.com/`. Desplegar tal cual envía la información de cartera a Render/Cloudflare. Ver `despliegue.md` (modo local recomendado). |
| R3 | **CORS abierto** | MEDIA | `app/main.py`: `allow_origins=["*"]` + `allow_credentials=True`. Innecesario en esquema same-origin; amplía la superficie de consumo desde navegadores arbitrarios. |
| R4 | **Token en `localStorage`** | MEDIA | `frontend/src/api/client.ts` usa `localStorage["cobranzas_token"]`. Expuesto ante cualquier XSS en el origen. |
| R5 | **Depuración residual con token en logs** | MEDIA | `frontend/src/auth/AuthContext.tsx` (~líneas 50-55) imprime la respuesta y el token con `console.log`. |
| R6 | **Sin rate-limiting en `/auth/login`** | MEDIA | Endpoint público sin límite de intentos; mitigable también en el reverse proxy/WAF. |
| R7 | **Contenedores como root** | MEDIA | Los `Dockerfile` no incluyen `USER` no-root. |
| R8 | **Sin backups ni monitoreo automatizados** | MEDIA | Solo dependen de procedimiento manual/cron no implementado; no hay métricas/alertas (solo `GET /health`). |
| R9 | **Subida validada por extensión** | BAJA/MEDIA | `routers/cargas.py` valida `.xlsx` por nombre; el contenido se parsea (invalida → `400`), pero no hay firma MIME ni límite de filas. `client_max_body_size 20m` acota el tamaño. |
| R10 | **Secretos de BD por defecto en Compose** | BAJA | Fallback `cobranzas/cobranzas` en `docker-compose.yml`. Solo red interna, pero se vuelve riesgo si se publica el puerto. |

---

## 3. Deuda técnica

| Ítem | Área | Detalle / evidencia |
|------|------|----------------------|
| D1 | Frontend | `console.log` de debug con el token (`AuthContext.tsx`). |
| D2 | Config | `VITE_API_BASE` declarada en Compose pero no consumida (el prefijo `/api` es fijo en `src/api/client.ts`). |
| D3 | Config | Dos definiciones de directorio de uploads: `config.upload_dir` (usado por `conciliacion_service.py:188`) y `core/paths.UPLOAD_DIR` (sin uso actual). |
| D4 | Arquitectura | Módulo de **conciliación** desactivado: modelos/schemas/servicios sin uso, tablas en la BD, y un `test_conciliacion…pyc` huérfano en `tests/__pycache__/` (fuente eliminada). Aumenta la superficie de confusión. |
| D5 | Persistencia | La carga por operador **no persiste auditoría** (decisión documentada en `docs/cargas.md`), pero deja sin trazabilidad los cambios masivos. A confirmar si es aceptable para la empresa. |
| D6 | Acceso a datos | Varias queries se arman directo en `routers/`/`seed` (`db.scalar/select`, `db.query`) en vez de `repositories/` (contradice parcialmente la convención de `docs/arquitectura.md`). |
| D7 | Config | `nginx.conf` embebido en la imagen: cambiar el destino de la API exige rebuild del contenedor (no hay variable de entorno). |
| D8 | Infra | Sin pipeline CI/CD, sin `lint` automatizado, sin verificación de migraciones en CI. |
| D9 | Runtime | Backend sin `--reload` en el entrypoint (esperable en prod), pero tampoco hay opción de hot-reload por defecto para desarrollo con Docker. |
| D10 | Seguridad | No hay refresh token ni forma de revocar sesiones puntuales; rotar `SECRET_KEY` invalida todo de golpe. No hay bloqueo por intentos fallidos. |

---

## 4. Recomendaciones priorizadas

### Prioridad ALTA (hacer antes del pase a producción)

| Recomendación | Impacto | Esfuerzo |
|---------------|---------|----------|
| 1. Inyectar siempre `SECRET_KEY`/`POSTGRES_PASSWORD` aleatorios (blindar `.env`; añadir validación de que no se esté usando el valor por defecto). | Evita falsificación de JWT y compromiso de la BD | Bajo |
| 2. Eliminar los `console.log` de `AuthContext.tsx`. | No exponer tokens/sesiones en consola | Trivial |
| 3. Decidir topología: **modo local** para producción (cambiar `nginx.conf` a `proxy_pass http://backend:8000/`) o, si se conserva backend externo, evaluar privacidad/DATOS y acordar contrato con el proveedor. | Datos bajo control de la empresa | Bajo |
| 4. Terminar HTTPS siempre (reverse proxy del host) y restringir CORS al origen real (o eliminarlo en same-origin). | Protege credenciales y reduce superficie | Bajo/Medio |
| 5. Automatizar backups (cron `pg_dump` + copia fuera de la máquina) y verificación de restauración. | Recuperación ante desastre | Bajo |
| 6. Contenedores no-root (`USER` en los `Dockerfile`). | Reduce impacto de un compromiso | Bajo |

### Prioridad MEDIA (siguiente iteración)

| Recomendación | Esfuerzo |
|---------------|----------|
| 7. Rate-limiting en `/auth/login` (o equivalente en WAF/reverse proxy) + bloqueo por intentos fallidos. | Bajo/Medio |
| 8. Mover el token a cookie `HttpOnly`+`Secure`+`SameSite` con protección CSRF, o implementar refresh + revocación. | Medio/Alto |
| 9. Validar firma/MIME real del XLSX y límite de filas; acotar y auditar el directorio de uploads. | Bajo |
| 10. Monitoreo mínimo: chequeo externo de `/api/health` con alarma + `docker compose ps` y disco (hoy es manual). | Bajo |
| 11. CI básico: `pytest` + build de frontend + drift-check de Alembic en cada push. | Medio |
| 12. Confirmar con negocio la ausencia de auditoría en la carga por operador (D5) y decidir si registrar un historial de cargas. | Bajo/Medio |

### Prioridad BAJA (mantenimiento)

| Recomendación | Esfuerzo |
|---------------|----------|
| 13. Consumir `VITE_API_BASE` (o eliminarla de Compose). | Trivial |
| 14. Unificar `UPLOAD_DIR` (eliminar `core/paths.py` o usarlo en todos lados). | Bajo |
| 15. Eliminar/limpiar el código y los `.pyc` huérfanos del módulo de conciliación o documentar su reactivación. | Bajo |
| 16. Mover las queries directas a `repositories/`. | Medio |
| 17. Parametrizar el destino del proxy (`frontend/nginx.conf`) con env o templating. | Bajo |
| 18. Política de contraseñas y renovación; auditoría de inicios de sesión fallidos. | Bajo |

---

## 5. Notas de la verificación

- **Tests**: suite completa verde en el contenedor (`docker compose exec backend pytest -q`).
- **Incidente 502**: causa raíz confirmada como ausencia de SNI en el proxy HTTPS hacia Cloudflare/Render; se documenta la reproducción y la solución en `troubleshooting.md` (sección 1).
- **Consistencia de la documentación**: las rutas, puertos, variables y comandos citados en `docs/` fueron contrastados contra `docker-compose.yml`, los `Dockerfile`, `config.py`, `entrypoint.sh` y los routers reales.
- **No se modificó código funcional** como parte de esta auditoría; los cambios realizados son de documentación y un comentario de contexto en `frontend/nginx.conf`.
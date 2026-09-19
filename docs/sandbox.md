# Modo demo / sandbox

El sistema incluye un **modo demo** para conocer la aplicación sin credenciales y sin riesgo sobre los datos reales. Una sesión demo es:

- **Anónima**: se entra desde la pantalla de login con un clic ("Demo · Operador" / "Demo · Supervisor"), sin usuario ni contraseña.
- **De solo lectura**: el backend rechaza toda escritura de una sesión demo con `403` (mensaje "El modo demo es de solo lectura…"). En el frontend, las acciones de escritura se ocultan o deshabilitan.
- **Efímera**: expira automáticamente por **TTL absoluto** en Redis (default `3600`s ≈ 1 hora). El TTL se fija al crear la sesión y **nunca se renueva**, pase lo que pase con la actividad.

## Cómo funciona

### Flujo de una sesión demo

1. `POST /auth/demo/login` con body `{ "rol": "OPERADOR" | "SUPERVISOR" }` no requiere credenciales.
2. El backend construye un **snapshot de datos demo** (ver `sandbox/seed.py`), lo guarda en Redis bajo la clave `demo:{session_id}` con `EX = SANDBOX_TTL_SECONDS`, y emite un JWT con `tipo: "DEMO"` cuyos claims (`sandbox:{session_id}`) viven con el mismo TTL.
3. El resto de las rutas funciona igual: el token `tipo: DEMO` se autentica contra Redis en lugar de PostgreSQL. Si la sesión expiró, devuelve `401`. Si Redis no responde, devuelve `503`.

### Datos demo (seed)

| Qué | Cant. / valor |
|---|---|
| Tipos de operación | `PROMESA_PAGO`, `DEUDA_BONIFICADA` |
| Motivos de carga | 2 |
| Períodos | 4; **Septiembre 2026** es el vigente |
| Operadores | `demo.opera` (operador A) y `demo.operaB` (operador B) |
| Gestiones | 11 (`demo-g-1` … `demo-g-11`): 8 en septiembre (g1‑g8) y 3 en octubre (g9‑g11) |
| Historial | para `demo-g-1`, `demo-g-2` y `demo-g-3` |
| Alertas | calculadas con la misma regla del modo real (`domain.alertas`) |

Alcance por perfil:

- **Operador demo** (`demo-op-a`): ve **6** gestiones (g1‑g5 en septiembre + g9 en octubre). Su dashboard de septiembre muestra 5.
- **Supervisor demo**: ve las **11** gestiones y todos los catálogos.

Ambos perfiles listan en `/usuarios` los 2 operadores demo. Un operador demo no puede listar usuarios (referencia a tabla real, solo para supervisor) ni acceder a gestiones ajenas → `403`.

### Aislamiento

- Los datos demo viven **solo en Redis**; la base PostgreSQL (datos reales) no se toca.
- Cada sesión genera su propio snapshot (`demo:{id}`), por lo que dos sesiones demo son totalmente independientes.
- Los IDs demo (`demo-*`) no colisionan con los UUID reales.

## TTL absoluto

El TTL se mide al **crear** la sesión y no se renueva con el uso. Esto evita sesiones demo "vivas para siempre"; a los `SANDBOX_TTL_SECONDS` el token deja de ser válido y el usuario vuelve a la pantalla de login (el frontend muestra un aviso de sesión expirada).

## Redis caído

La disponibilidad del modo demo depende de Redis. Si Redis no responde:

- `POST /auth/demo/login` → `503` ("El servicio de demostración no está disponible en este momento.").
- Cualquier rutina con sesión demo → `503`.
- **El modo real no se ve afectado**: la autenticación normal consulta PostgreSQL directamente y no depende de Redis (por eso `depends_on` de Compose es solo `service_started`, orden de arranque, no de salud).

`POST /auth/demo/logout` elimina `sandbox:{id}` y `demo:{id}`; es idempotente aunque Redis esté caído.

## Arquitectura (backend)

```
app/sandbox/
├── principal.py   # dataclass Principal (tipo REAL/DEMO) que reemplaza al ORM en auth
├── store.py       # SandboxStore: claves sandbox:{id} (claims) y demo:{id} (datos) con ex=ttl
├── seed.py        # construccion_datos_demo(): snapshot de ejemplo
├── reader.py      # DemoReader: lecturas demo (gestiones, periodos, catálogos, dashboards)
├── service.py     # SandboxService: crear_sesion / cerrar_sesion / obtener
├── schemas.py     # DemoLoginRequest (rol)
└── deps.py        # bloquear_demo (403), get_reader_demo, MENSAJE_SOLO_LECTURA
```

- `core/deps.py`: `get_current_usuario` devuelve un `Principal`; rama DEMO lee claims desde `SandboxStore`, rama REAL consulta por `SessionLocal()` directamente.
- `core/security.py`: `create_access_token(subject, rol, tipo="REAL")` agrega el claim `tipo`. Los tokens ya emitidos sin `tipo` se leen como `REAL` (retrocompatible).
- `schemas/usuario.py`: `UsuarioOut.tipo` distingue `"REAL"` / `"DEMO"` (los objetos demo de las rutas también lo incluyen).
- Las rutas de lectura (`/destacadas`, `/periodos`, `/gestiones`, `/dashboard/*`, `/cargas/resumen`) tienen rama demo vía `get_reader_demo`; las de escritura usan `bloquear_demo`.

## Frontend

- `pages/Login.tsx`: botones "Demo · Operador" y "Demo · Supervisor"; aviso si la sesión expiró.
- `api/client.ts`: ante un `401` con token presente, limpia el token y emite el evento `cobranzas_sesion_expirada`.
- `auth/AuthContext.tsx`: `ingresarDemo(rol)`; escucha el evento de sesión expirada.
- `App.tsx` / `styles.css`: badge **DEMO** en la barra lateral y banner "Modo demostración…" en el contenido.
- `pages/{Gestiones,Dashboard,Operadores}.tsx`: cuando `usuario.tipo === "DEMO"` se ocultan acciones de escritura y las celdas editables de la tabla se vuelven de solo lectura.

## Configuración

| Variable | Default | Descripción |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379` | Conexión a Redis (servicio `redis` de Compose) |
| `SANDBOX_TTL_SECONDS` | `3600` | TTL absoluto (segundos) de las sesiones demo |

## Tests

La suite del sandbox usa **fakeredis** y un TestClient propio (sin PostgreSQL), salvo un test que verifica que el flujo real no depende de Redis con Redis caído (se omite si no hay BD).

```bash
docker compose run --rm --entrypoint pytest backend tests/test_sandbox.py -q
docker compose run --rm --entrypoint pytest backend tests/ -q
```
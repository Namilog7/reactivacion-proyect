# Modelo de datos

![Entidades](no hay diagrama: tablas listadas abajo)

| Tabla | Propósito | Campos destacados |
|-------|-----------|-------------------|
| `usuarios` | Usuarios del sistema | `username` (único), `password_hash`, `nombre`, `rol` (`rol_enum`: SUPERVISOR/OPERADOR), `activo` |
| `periodos` | Períodos de cobranza | `nombre`, `mes`, `anio`, `periodo_vigente` (un solo período vigente gestionado por el supervisor) |
| `clientes` | Clientes de la cartera | `numero` (único), `nombre` |
| `tipos_operacion` | Catálogo extensible de tipos | `codigo` (único p. ej. `PROMESA_PAGO`, `DEUDA_BONIFICADA`), `nombre` |
| `motivos_conciliacion` | Catálogo extensible de motivos | `codigo` (único p. ej. `PAGOS`, `DEUDAS_SIN_NC`), `nombre` |
| `gestiones` | Gestión de un cliente en un período | `cliente_id`, `operador_id`, `periodo_id`, `tipo_operacion_id`, `fecha_ofrecida_pago`, `pago`, `desbloqueado`, `tiene_nc`, `observaciones`, `origen` (`origen_gestion_enum`: MANUAL/CONCILIACION), `conciliacion_origen_id`. **Único** `(cliente_id, periodo_id)` |
| `conciliaciones` | Importación/previsualización/confirmación de archivos | `numero` (correlativo), `supervisor_id`, `periodo_id`, `motivo_id`, `estado` (`estado_conciliacion_enum`), `archivo_nombre`, `archivo_ruta`, `archivo_hash` (SHA-256), contadores (`registros_procesados`, `coincidencias`, `inconsistentes`, `clientes_inexistentes`, `duplicados`, `invalidos`, `modificaciones`), `error_mensaje` |
| `registros_conciliacion` | Fila por fila del archivo | `conciliacion_id`, `fila`, `cliente_numero`, `tipo_operacion_archivo`, `tipo_operacion_id` (si se reconoce), `categoria`, `gestion_id` (si aplica), `estado_anterior`/`estado_posterior` (JSONB snapshot al confirmar, sólo si hubo modificación), `mensaje` |
| `historial_cambios` | Auditoría de cambios en gestiones | `gestion_id`, `usuario_id`, `conciliacion_id` (origen automático), `campo` (`campo_cambio_enum` minúscula: `creacion`, `operador`, `tipo_operacion`, `fecha_ofrecida_pago`, `pago`, `desbloqueado`, `tiene_nc`, `observaciones`), `valor_anterior`/`valor_nuevo` (JSONB), `origen` (`origen_cambio_enum`: `OPERADOR_MANUAL`, `SUPERVISOR_MANUAL`, `CONCILIACION`) |

> Las tablas `conciliaciones` y `registros_conciliacion` y el catálogo `motivos_conciliacion` se conservan tal como fueron migradas, pero el módulo de conciliación está **desactivado** por ahora: no hay API ni UI. La carga por operador no persiste nada (los motivos viven en `app/domain/cargas.py`).

## Enums (base de datos)

| Enum | Valores |
|------|---------|
| `rol_enum` | `SUPERVISOR`, `OPERADOR` |
| `origen_gestion_enum` | `MANUAL`, `CONCILIACION` |
| `estado_conciliacion_enum` | `PREVISUALIZACION`, `PROCESANDO`, `COMPLETADA`, `ERROR` |
| `campo_cambio_enum` | `creacion`, `operador`, `tipo_operacion`, `fecha_ofrecida_pago`, `pago`, `desbloqueado`, `tiene_nc`, `observaciones` |
| `origen_cambio_enum` | `OPERADOR_MANUAL`, `SUPERVISOR_MANUAL`, `CONCILIACION` |

> Las categorías de registro de conciliación (`COINCIDENCIA`, `CLIENTE_SIN_GESTION`, `INCONSISTENTE`, `DUPLICADO`, `INVALIDO`) se almacenan como texto (`registros_conciliacion.categoria`).

## Relaciones principales

- `gestiones.n` ⟶ `clientes.1`, `periodos.1`, `usuarios.1` (operador), `tipos_operacion.1`
- `conciliaciones.n` ⟶ `periodos.1`, `usuarios.1` (supervisor), `motivos_conciliacion.1`
- `registros_conciliacion.n` ⟶ `conciliaciones.1`, `gestiones.1` (nullable)
- `historial_cambios.n` ⟶ `gestiones.1`, `usuarios.1` (nullable), `conciliaciones.1` (nullable)
# Carga de archivos por operador

Sustituye al flujo de conciliación: el **supervisor** sube un archivo XLSX **por operador** e indica el **motivo** de la carga. El sistema actualiza las gestiones de ese operador en el período (vigente por defecto) según el motivo. No se persiste auditoría ni historial.

## Flujo

1. El supervisor abre **Operadores** y ve el mapa con una tarjeta por operador (gestiones, pagos, alertas y críticas del período vigente).
2. Pulsa **Subir archivo…** en la tarjeta del operador, elige el **motivo** y el archivo `.xlsx` (solo números de cliente; el encabezado es opcional).
3. `POST /cargas` con `multipart/form-data`: `file`, `operador_id`, `motivo` (y opcionalmente `periodo_id`).
4. El backend procesa y devuelve el resumen; el mapa se refresca.

## Motivos y campos que actualizan

| Código | Nombre | Cambios sobre la gestión |
|--------|--------|--------------------------|
| `PAGO_DESBLOQUEO` | Pago y desbloqueo (reactivado) | `pago = true`, `desbloqueado = true` |
| `PAGO_SIN_DESBLOQUEO` | Pago sin desbloqueo | `pago = true` |
| `DEUDA_SIN_NC` | Deuda sin nota de crédito | `tiene_nc = false` |
| `DEUDA_SIN_NC_SIN_DESBLOQUEO` | Deuda sin nota de crédito ni desbloqueo | `tiene_nc = false`, `desbloqueado = false` |

- Los motivos de **deuda** no modifican `pago`.
- Si el valor ya coincide, la fila cuenta como *sin cambios*.
- La semántica vive en `app/domain/cargas.py` (idempotente: solo cambia lo que difiere).

## Comportamiento por fila

Para cada número de cliente del archivo:

- Si el cliente no tiene **gestión de ese operador en el período** → se ignora y suma al contador `sin_gestion` (no se crean gestiones ni clientes).
- Si hay gestión y el motivo implica cambios → se actualizan los flags (`modificaciones`) y cuenta como `actualizada`.
- Si hay gestión pero ya estaba en el estado objetivo → `sin_cambios`.

El archivo se lee en memoria (no se guarda). Duplicados o filas vacías dentro del archivo se cuentan en `duplicados_archivo` / `invalidas_archivo`.

## Respuesta de `POST /cargas`

```
operador, periodo, motivo (código + nombre), archivo_nombre,
total_filas, duplicados_archivo, invalidas_archivo,
procesadas, actualizadas, sin_cambios, sin_gestion, modificaciones
```

## Verificación

- `GET /cargas/resumen` → por operador en el período vigente: `gestiones`, `pagos`, `alertas`, `criticas`.
- `GET /cargas/motivos` → catálogo de motivos para el selector.

Restricciones: solo `SUPERVISOR`. El archivo debe ser `.xlsx`. Si no hay período vigente, la carga devuelve 400.
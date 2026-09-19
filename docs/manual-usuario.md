# Manual de usuario

## Qué es el sistema

Es la herramienta interna para registrar y dar seguimiento a las **gestiones de cobranza**: cada cliente en cada período de cobranza tiene una gestión con su estado (pago, desbloqueo de servicio, nota de crédito, tipo de operación) y un **historial** de los cambios hechos. Además, el supervisor puede aplicar **cargas por lotes** desde archivos Excel y el sistema **alerta** sobre situaciones anómalas.

> Este manual no requiere conocimientos técnicos. El acceso es **dentro de la red de la empresa** vía navegador.

## Identificarse

1. Abrir la URL que defina la empresa (en desarrollo: `http://localhost:8080`).
2. Ingresar **usuario** y **contraseña**.
3. Según el rol verás un menú distinto:

| Rol | Qué puede hacer |
|-----|-----------------|
| **OPERADOR** | Ver y gestionar **sus propios clientes** del período; consultar su dashboard. |
| **SUPERVISOR** | Ver todo: clientes de todos los operadores, usuarios, períodos, cargas por lote y resúmenes globales. |

Si la contraseña queda bloqueada o olvidada, contactar al supervisor (la app no permite auto-recuperación).

## Pantallas

### Dashboard (panel de inicio)

- **Operador**: resumen de **su** trabajo en el período vigente — cantidad gestiones, pagos, alertas, críticas y los problemas de nota de crédito / desbloqueo. Puede elegir otro período si necesita.
- **Supervisor**: visión global — operadores (total/activos), períodos, total de gestiones y el detalle de gestiones por período.

### Gestiones (ficha del cliente)

Es la pantalla central. Permite:

- **Buscar/filtrar**: por período, operador (solo supervisor), texto (número/razón), tipo de operación y estado (pago, desbloqueo, nota de crédito, alerta). Resultados paginados.
- **Ver el detalle** de una gestión: cliente, tipo de operación, fecha de pago ofrecida, observaciones, **alertas** y **historial** de cambios.
- **Crear/editar** una gestión (un cliente solo puede tener una gestión por período; si ya existe, se edita la existente).
- **Quién ve qué**: un operador solo ve/edita sus gestiones; el supervisor ve y edita todas.

### Operadores y carga de archivos (solo supervisor)

- Se muestra una **tarjeta por operador** con el resumen del período vigente (gestiones, pagos, alertas, críticas).
- El supervisor puede **subir una planilla Excel** (`.xlsx`) con **números de cliente** (una columna; el encabezado es opcional) e indicar el **motivo** de la carga:

| Motivo | Qué hace |
|--------|----------|
| **Pago y desbloqueo** | Marca el cliente como pagado y desbloqueado (reactivación completa). |
| **Pago sin desbloqueo** | Marca solo el pago. |
| **Deuda sin nota de crédito** | Marca que la deuda aún no tiene nota de crédito. |
| **Deuda sin NC ni desbloqueo** | Marca que falta nota de crédito y el desbloqueo. |

- Solo se actualizan los clientes que **tienen gestión del operador en ese período**. Los que no tienen, se listan como "sin gestión" y no se tocan (no se crean gestiones automáticamente).
- La planilla **no se guarda** en el sistema: solo se aplican los cambios.

## Qué significa cada alerta

El sistema marca con **"Alerta"** (⚠) o **"CRÍTICA"** (‼) ciertas combinaciones que la regla de negocio considera inconsistentes:

1. **Pagó sin nota de crédito** → alerta de NC.
2. **Pagó sin desbloqueo** → alerta de desbloqueo.
3. **Deuda bonificada sin nota de crédito** → alerta de NC.
4. **Situación crítica**: pago de deuda bonificada sin nota de crédito y con desbloqueo → **CRÍTICA**.

Hacer clic sobre el indicador (o la celda coloreada) muestra el detalle del motivo. Las alertas son informativas, pero **CRÍTICA** debería revisarse en el día.

## Buenas prácticas

- Registrar la **observación** y la **fecha de pago ofrecida** cuando corresponda: quedan en el historial.
- No crear gestiones duplicadas para un mismo cliente en el mismo período: el sistema rechaza la segunda (aviso "ya existe").
- El supervisor valida los archivos `.xlsx` **antes** de cargarlos: números de cliente correctos y un solo motivo por archivo.
- Al terminar la jornada, cerrar sesión si se comparte la estación de trabajo.

## Preguntas frecuentes

- **¿Puedo ver gestiones de otro compañero?** No, salvo que seas supervisor.
- **¿Puedo borrar una gestión?** La app no permite eliminación definitiva; se corrige la gestión y el cambio queda registrado.
- **¿Qué pasa si subo un archivo con el operador equivocado?** Nada se modifica de otros operadores: el archivo solo afecta gestiones del operador elegido.
- **¿Se guardan mis archivos?** No; solo se aplican los cambios sobre los datos.
- **¿Cuándo cambia el "período vigente"?** Cuando el supervisor crea el período nuevo y lo activa.
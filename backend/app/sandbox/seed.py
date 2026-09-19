"""Datos ficticios de la sesión de demostración.

Los datos se generan en memoria al abrir cada sesión demo y se guardan en
Redis bajo `demo:{sandbox_id}`. Nunca se escriben en PostgreSQL.

Los identificadores usan el prefijo `demo-` para que jamás colisionen con
los UUIDs del sistema real. Las combinaciones de gestiones ejercitan todas
las reglas de alerta del dominio (ver app/domain/alertas.py).
"""

from app.domain.alertas import evaluar_alertas

TIPOS_OPERACION = [
    {"id": "demo-to-promesa", "codigo": "PROMESA_PAGO", "nombre": "Promesa de pago"},
    {"id": "demo-to-bonificada", "codigo": "DEUDA_BONIFICADA", "nombre": "Deuda bonificada"},
]

MOTIVOS = [
    {
        "id": "demo-mo-pagos",
        "codigo": "PAGOS",
        "nombre": "Pagos",
        "descripcion": "El archivo representa clientes que pagaron. Se actualiza el estado de pago.",
    },
    {
        "id": "demo-mo-deudas",
        "codigo": "DEUDAS_SIN_NC",
        "nombre": "Deudas sin notas de crédito",
        "descripcion": "El archivo representa deudas que aún no tienen nota de crédito.",
    },
]

PERIODOS = [
    {"id": "demo-p-ago", "nombre": "Agosto 2026", "mes": 8, "anio": 2026, "periodo_vigente": False},
    {"id": "demo-p-sep", "nombre": "Septiembre 2026", "mes": 9, "anio": 2026, "periodo_vigente": True},
    {"id": "demo-p-oct", "nombre": "Octubre 2026", "mes": 10, "anio": 2026, "periodo_vigente": False},
    {"id": "demo-p-nov", "nombre": "Noviembre 2026", "mes": 11, "anio": 2026, "periodo_vigente": False},
]

OPERADORES = [
    {
        "id": "demo-op-a",
        "username": "demo.opera",
        "nombre": "Operador Demo",
        "rol": "OPERADOR",
        "activo": True,
        "created_at": "2026-08-01T09:00:00+00:00",
        "tipo": "DEMO",
    },
    {
        "id": "demo-op-b",
        "username": "demo.operaB",
        "nombre": "Operador Demo B",
        "rol": "OPERADOR",
        "activo": True,
        "created_at": "2026-08-01T09:00:00+00:00",
        "tipo": "DEMO",
    },
]

SUPERVISOR_DEMO = {"username": "demo.supervisor", "nombre": "Supervisor Demo"}

_GESTIONES_RAW = [
    dict(
        id="demo-g-1", cliente="900001", operador="demo-op-a", periodo="demo-p-sep",
        tipo="PROMESA_PAGO", pago=False, desbloqueado=False, tiene_nc=False,
        fecha=None, obs="Sin novedades. Cliente sin estado registrado.",
        creada="2026-09-02T10:00:00+00:00", actualizada="2026-09-02T10:05:00+00:00",
    ),
    dict(
        id="demo-g-2", cliente="900002", operador="demo-op-a", periodo="demo-p-sep",
        tipo="DEUDA_BONIFICADA", pago=True, desbloqueado=True, tiene_nc=False,
        fecha=None, obs="Situación crítica: pago registrado sin nota de crédito.",
        creada="2026-09-03T09:00:00+00:00", actualizada="2026-09-05T11:00:00+00:00",
    ),
    dict(
        id="demo-g-3", cliente="900003", operador="demo-op-a", periodo="demo-p-sep",
        tipo="PROMESA_PAGO", pago=True, desbloqueado=False, tiene_nc=True,
        fecha="2026-09-15", obs="El cliente pagó pero sigue sin desbloquearse.",
        creada="2026-09-04T08:20:00+00:00", actualizada="2026-09-15T09:10:00+00:00",
    ),
    dict(
        id="demo-g-4", cliente="900004", operador="demo-op-a", periodo="demo-p-sep",
        tipo="DEUDA_BONIFICADA", pago=False, desbloqueado=False, tiene_nc=False,
        fecha=None, obs="Deuda bonificada sin nota de crédito.",
        creada="2026-09-04T08:30:00+00:00", actualizada="2026-09-04T08:30:00+00:00",
    ),
    dict(
        id="demo-g-5", cliente="900005", operador="demo-op-a", periodo="demo-p-sep",
        tipo="PROMESA_PAGO", pago=True, desbloqueado=False, tiene_nc=False,
        fecha=None, obs="Pagó sin desbloqueo y sin nota de crédito.",
        creada="2026-09-05T12:00:00+00:00", actualizada="2026-09-06T10:00:00+00:00",
    ),
    dict(
        id="demo-g-6", cliente="900006", operador="demo-op-b", periodo="demo-p-sep",
        tipo="DEUDA_BONIFICADA", pago=True, desbloqueado=True, tiene_nc=True,
        fecha="2026-09-20", obs="Todo en orden: pago, desbloqueo y nota de crédito.",
        creada="2026-09-08T09:00:00+00:00", actualizada="2026-09-20T10:00:00+00:00",
    ),
    dict(
        id="demo-g-7", cliente="900007", operador="demo-op-b", periodo="demo-p-sep",
        tipo="PROMESA_PAGO", pago=True, desbloqueado=True, tiene_nc=True,
        fecha="2026-09-18", obs="Todo en orden.",
        creada="2026-09-08T09:05:00+00:00", actualizada="2026-09-18T12:00:00+00:00",
    ),
    dict(
        id="demo-g-8", cliente="900008", operador="demo-op-b", periodo="demo-p-sep",
        tipo="PROMESA_PAGO", pago=False, desbloqueado=False, tiene_nc=False,
        fecha=None, obs="", creada="2026-09-10T11:00:00+00:00", actualizada="2026-09-10T11:00:00+00:00",
    ),
    dict(
        id="demo-g-9", cliente="900003", operador="demo-op-a", periodo="demo-p-oct",
        tipo="DEUDA_BONIFICADA", pago=False, desbloqueado=False, tiene_nc=False,
        fecha=None, obs="Mismo cliente que septiembre: cada período es independiente.",
        creada="2026-10-01T09:00:00+00:00", actualizada="2026-10-01T09:00:00+00:00",
    ),
    dict(
        id="demo-g-10", cliente="900006", operador="demo-op-b", periodo="demo-p-oct",
        tipo="PROMESA_PAGO", pago=False, desbloqueado=False, tiene_nc=False,
        fecha="2026-10-05", obs="", creada="2026-10-02T09:00:00+00:00", actualizada="2026-10-02T09:00:00+00:00",
    ),
    dict(
        id="demo-g-11", cliente="900002", operador="demo-op-b", periodo="demo-p-oct",
        tipo="DEUDA_BONIFICADA", pago=True, desbloqueado=True, tiene_nc=False,
        fecha=None, obs="Situación crítica también en octubre.",
        creada="2026-10-03T10:00:00+00:00", actualizada="2026-10-03T10:00:00+00:00",
    ),
]

_HISTORIAL = {
    "demo-g-1": [
        {
            "id": "demo-h-1",
            "usuario_nombre": "Operador Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "creacion",
            "valor_anterior": None,
            "valor_nuevo": {},
            "origen": "OPERADOR_MANUAL",
            "created_at": "2026-09-02T10:00:00+00:00",
        },
        {
            "id": "demo-h-2",
            "usuario_nombre": "Operador Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "observaciones",
            "valor_anterior": {"value": ""},
            "valor_nuevo": {"value": "Sin novedades. Cliente sin estado registrado."},
            "origen": "OPERADOR_MANUAL",
            "created_at": "2026-09-02T10:05:00+00:00",
        },
    ],
    "demo-g-2": [
        {
            "id": "demo-h-3",
            "usuario_nombre": "Supervisor Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "creacion",
            "valor_anterior": None,
            "valor_nuevo": {},
            "origen": "SUPERVISOR_MANUAL",
            "created_at": "2026-09-03T09:00:00+00:00",
        },
        {
            "id": "demo-h-4",
            "usuario_nombre": "Supervisor Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "tipo_operacion",
            "valor_anterior": {"value": "PROMESA_PAGO"},
            "valor_nuevo": {"value": "DEUDA_BONIFICADA"},
            "origen": "SUPERVISOR_MANUAL",
            "created_at": "2026-09-03T09:30:00+00:00",
        },
        {
            "id": "demo-h-5",
            "usuario_nombre": "Supervisor Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "pago",
            "valor_anterior": {"value": False},
            "valor_nuevo": {"value": True},
            "origen": "SUPERVISOR_MANUAL",
            "created_at": "2026-09-05T11:00:00+00:00",
        },
    ],
    "demo-g-3": [
        {
            "id": "demo-h-6",
            "usuario_nombre": "Operador Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "creacion",
            "valor_anterior": None,
            "valor_nuevo": {},
            "origen": "OPERADOR_MANUAL",
            "created_at": "2026-09-04T08:20:00+00:00",
        },
        {
            "id": "demo-h-7",
            "usuario_nombre": "Operador Demo",
            "conciliacion_id": None,
            "num_conciliacion": None,
            "campo": "fecha_ofrecida_pago",
            "valor_anterior": None,
            "valor_nuevo": {"value": "2026-09-15"},
            "origen": "OPERADOR_MANUAL",
            "created_at": "2026-09-15T09:10:00+00:00",
        },
    ],
}


def _gestion(raw: dict, operador_nombre: str, periodo_nombre: str, tipo: dict) -> dict:
    ev = evaluar_alertas(
        tipo_operacion_codigo=tipo["codigo"],
        pago=raw["pago"],
        tiene_nc=raw["tiene_nc"],
        desbloqueado=raw["desbloqueado"],
    )
    return {
        "id": raw["id"],
        "cliente_numero": raw["cliente"],
        "cliente_nombre": f"Cliente Demo {raw['cliente']}",
        "operador": {"id": raw["operador"], "nombre": operador_nombre},
        "periodo_id": raw["periodo"],
        "periodo_nombre": periodo_nombre,
        "tipo_operacion": {"id": tipo["id"], "codigo": tipo["codigo"], "nombre": tipo["nombre"]},
        "fecha_ofrecida_pago": raw["fecha"],
        "pago": raw["pago"],
        "desbloqueado": raw["desbloqueado"],
        "tiene_nc": raw["tiene_nc"],
        "observaciones": raw["obs"],
        "origen": "MANUAL",
        "conciliacion_origen_id": None,
        "alertas": {**ev, "nivel": ev["nivel"].value},
        "created_at": raw["creada"],
        "updated_at": raw["actualizada"],
    }


def construir_datos_demo() -> dict:
    """Construye el snapshot completo de datos ficticios de una sesión demo."""
    operadores = {o["id"]: o for o in OPERADORES}
    periodos = {p["id"]: p for p in PERIODOS}
    tipos = {t["codigo"]: t for t in TIPOS_OPERACION}
    gestiones = [
        _gestion(
            raw,
            operador_nombre=operadores[raw["operador"]]["nombre"],
            periodo_nombre=periodos[raw["periodo"]]["nombre"],
            tipo=tipos[raw["tipo"]],
        )
        for raw in _GESTIONES_RAW
    ]
    return {
        "tipos_operacion": TIPOS_OPERACION,
        "motivos": MOTIVOS,
        "periodos": PERIODOS,
        "operadores": OPERADORES,
        "gestiones": gestiones,
        "historial": _HISTORIAL,
    }
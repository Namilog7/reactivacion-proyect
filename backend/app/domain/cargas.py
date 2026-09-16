"""Motivos de carga de archivos por operador (reemplaza a la conciliación).

El supervisor sube un .xlsx por operador e indica el motivo. Cada motivo
define QUÉ campos de las gestiones de ese operador se actualizan:

- PAGO_DESBLOQUEO:              el cliente pagó y fue reactivado -> pago=true, desbloqueado=true.
- PAGO_SIN_DESBLOQUEO:          el cliente pagó pero no fue reactivado -> pago=true.
- DEUDA_SIN_NC:                 deuda sin nota de crédito -> tiene_nc=false.
- DEUDA_SIN_NC_SIN_DESBLOQUEO:  deuda sin nota de crédito ni reactivación -> tiene_nc=false, desbloqueado=false.

Los motivos de deuda NO modifican el flag `pago`. La carga no persiste
auditoría ni historial: solo refleja los cambios en la vista del operador.
"""

from app.domain.conciliacion_reglas import CambioPendiente
from app.domain.enums import CampoCambio


def _pendientes(gestion, campos: list[tuple[CampoCambio, bool]]) -> list[CambioPendiente]:
    return [
        CambioPendiente(campo, valor)
        for campo, valor in campos
        if getattr(gestion, campo.value) != valor
    ]


MOTIVOS_CARGA: dict[str, dict] = {
    "PAGO_DESBLOQUEO": {
        "nombre": "Pago y desbloqueo (reactivado)",
        "descripcion": "El cliente pagó y su cuenta fue reactivada.",
        "aplicar": lambda g: _pendientes(
            g, [(CampoCambio.PAGO, True), (CampoCambio.DESBLOQUEADO, True)]
        ),
    },
    "PAGO_SIN_DESBLOQUEO": {
        "nombre": "Pago sin desbloqueo",
        "descripcion": "El cliente pagó pero la cuenta sigue bloqueada.",
        "aplicar": lambda g: _pendientes(g, [(CampoCambio.PAGO, True)]),
    },
    "DEUDA_SIN_NC": {
        "nombre": "Deuda sin nota de crédito",
        "descripcion": "El cliente mantiene una deuda sin nota de crédito.",
        "aplicar": lambda g: _pendientes(g, [(CampoCambio.TIENE_NC, False)]),
    },
    "DEUDA_SIN_NC_SIN_DESBLOQUEO": {
        "nombre": "Deuda sin nota de crédito ni desbloqueo",
        "descripcion": "El cliente mantiene una deuda, sin nota de crédito y sin reactivación.",
        "aplicar": lambda g: _pendientes(
            g, [(CampoCambio.TIENE_NC, False), (CampoCambio.DESBLOQUEADO, False)]
        ),
    },
}


def motivos_disponibles() -> list[dict]:
    return [
        {"codigo": codigo, "nombre": m["nombre"], "descripcion": m["descripcion"]}
        for codigo, m in MOTIVOS_CARGA.items()
    ]


def validar_motivo(codigo: str) -> str:
    if codigo not in MOTIVOS_CARGA:
        raise ValueError(f"Motivo de carga inválido: {codigo}")
    return codigo


def aplicar_motivo(codigo: str, gestion) -> list[CambioPendiente]:
    return MOTIVOS_CARGA[codigo]["aplicar"](gestion)
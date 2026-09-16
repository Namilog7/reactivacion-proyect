"""Reglas visuales de negocio (sección 7 del requerimiento).

Estas reglas viven UNA sola vez, en esta capa de dominio Python.
El backend las evalúa y las expone en la API; el frontend únicamente
las renderiza. Así se evita duplicarlas en JavaScript.

- Regla 1: pagó = true y tiene_nc = false  -> alerta en celda NC
- Regla 2: pagó = true y desbloqueado = false -> alerta en celda desbloqueo
- Regla 3: tipo = DEUDA_BONIFICADA y tiene_nc = false -> alerta en celda NC
- Regla 4: DEUDA_BONIFICADA y pagó y sin NC y desbloqueado -> alerta crítica
"""

from typing import TypedDict

from app.domain.enums import NivelAlerta

TIPO_DEUDA_BONIFICADA = "DEUDA_BONIFICADA"


class EvaluacionAlertas(TypedDict):
    nivel: NivelAlerta
    nc_alerta: bool
    desbloqueo_alerta: bool
    mensajes: list[str]


def evaluar_alertas(
    tipo_operacion_codigo: str,
    pago: bool,
    tiene_nc: bool,
    desbloqueado: bool,
) -> EvaluacionAlertas:
    """Evalúa las reglas de alerta para una gestión."""
    es_bonificada = tipo_operacion_codigo == TIPO_DEUDA_BONIFICADA
    mensajes: list[str] = []

    nc_alerta = (pago and not tiene_nc) or (es_bonificada and not tiene_nc)
    if pago and not tiene_nc:
        mensajes.append("Pagó sin nota de crédito (NC).")
    if es_bonificada and not tiene_nc:
        mensajes.append("Deuda bonificada sin nota de crédito (NC).")

    desbloqueo_alerta = pago and not desbloqueado
    if desbloqueo_alerta:
        mensajes.append("Pagó sin desbloqueo.")

    critica = es_bonificada and pago and not tiene_nc and desbloqueado
    if critica:
        mensajes.append(
            "Situación crítica: deuda bonificada, pago registrado, sin NC y desbloqueado."
        )

    if critica:
        nivel = NivelAlerta.CRITICA
    elif nc_alerta or desbloqueo_alerta:
        nivel = NivelAlerta.ALERTA
    else:
        nivel = NivelAlerta.NINGUNA

    return EvaluacionAlertas(
        nivel=nivel,
        nc_alerta=nc_alerta,
        desbloqueo_alerta=desbloqueo_alerta,
        mensajes=mensajes,
    )


def evaluar_gestion(gestion: dict) -> EvaluacionAlertas:
    """Evalúa alertas a partir de un dict de gestión (patrón DTO)."""
    return evaluar_alertas(
        tipo_operacion_codigo=gestion["tipo_operacion_codigo"],
        pago=bool(gestion["pago"]),
        tiene_nc=bool(gestion["tiene_nc"]),
        desbloqueado=bool(gestion["desbloqueado"]),
    )
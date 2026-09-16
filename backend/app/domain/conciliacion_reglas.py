"""Reglas/estrategias de conciliación (sección 15 del requerimiento).

Cada MOTIVO de conciliación tiene una estrategia que define QUÉ estado
de la gestión debe actualizarse. Son extensibles: para agregar un motivo
basta con crear una estrategia y registrarla en `ESTRATEGIAS`.

Reglas definidas:
- PAGOS:          el archivo representa clientes que pagaron -> pago = true.
- DEUDAS_SIN_NC:  el archivo representa deudas sin nota de crédito -> tiene_nc = false.

No se asume ningún otro cambio de estado que no esté definido aquí.
"""

from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import CampoCambio


@dataclass(frozen=True)
class CambioPendiente:
    campo: CampoCambio
    valor_nuevo: bool


class EstrategiaConciliacion(Protocol):
    def cambios(self, gestion) -> list[CambioPendiente]: ...


class PagoEstrategia:
    def cambios(self, gestion) -> list[CambioPendiente]:
        if not gestion.pago:
            return [CambioPendiente(CampoCambio.PAGO, True)]
        return []


class DeudaSinNCEstrategia:
    def cambios(self, gestion) -> list[CambioPendiente]:
        if gestion.tiene_nc:
            return [CambioPendiente(CampoCambio.TIENE_NC, False)]
        return []


class EstrategiaSinReglas:
    """Motivo registrado en BD pero sin estrategia definida: no modifica nada."""

    def cambios(self, gestion) -> list[CambioPendiente]:
        return []


ESTRATEGIAS: dict[str, EstrategiaConciliacion] = {
    "PAGOS": PagoEstrategia(),
    "DEUDAS_SIN_NC": DeudaSinNCEstrategia(),
}


def get_estrategia(codigo_motivo: str, default: EstrategiaConciliacion | None = None) -> EstrategiaConciliacion:
    if codigo_motivo in ESTRATEGIAS:
        return ESTRATEGIAS[codigo_motivo]
    # Motivos futuros sin estrategia: quedan "inertes" en lugar de romper.
    return default or EstrategiaSinReglas()


def aplicar_estrategia(codigo_motivo: str, gestion) -> list[CambioPendiente]:
    estrategia = get_estrategia(codigo_motivo)
    return estrategia.cambios(gestion)
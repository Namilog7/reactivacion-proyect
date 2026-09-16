from datetime import date, datetime

from sqlalchemy.orm import Session

from app.domain.enums import CampoCambio, OrigenCambio
from app.models.historial import HistorialCambio


def _json(v):
    """Asegura que los valores sean serializables a JSONB (fechas a ISO)."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _json(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_json(x) for x in v]
    return str(v)


class HistorialService:
    """Registra los cambios relevantes para auditoría (quién, cuándo, origen)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def registrar(
        self,
        gestion_id: str,
        campo: CampoCambio | str,
        valor_anterior,
        valor_nuevo,
        origen: OrigenCambio | str,
        usuario_id: str | None = None,
        conciliacion_id: str | None = None,
    ) -> None:
        self.db.add(
            HistorialCambio(
                gestion_id=gestion_id,
                usuario_id=usuario_id,
                conciliacion_id=conciliacion_id,
                campo=campo.value if isinstance(campo, CampoCambio) else str(campo),
                valor_anterior=_json(valor_anterior),
                valor_nuevo=_json(valor_nuevo),
                origen=origen.value if isinstance(origen, OrigenCambio) else str(origen),
            )
        )

    def listar(self, gestion_id: str) -> list[HistorialCambio]:
        from sqlalchemy import select

        from app.models.historial import HistorialCambio

        return list(
            self.db.scalars(
                select(HistorialCambio)
                .where(HistorialCambio.gestion_id == gestion_id)
                .order_by(HistorialCambio.created_at.desc())
            )
        )
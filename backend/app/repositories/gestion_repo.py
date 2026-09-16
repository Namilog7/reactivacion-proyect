from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.gestion import Gestion


class GestionRepo:
    @staticmethod
    def get(db: Session, gestion_id: str) -> Gestion | None:
        return db.get(Gestion, gestion_id)

    @staticmethod
    def get_by_cliente_periodo(
        db: Session, cliente_id: str, periodo_id: str
    ) -> Gestion | None:
        return db.scalar(
            select(Gestion).where(
                Gestion.cliente_id == cliente_id,
                Gestion.periodo_id == periodo_id,
            )
        )

    @staticmethod
    def exists_cliente_periodo(db: Session, cliente_id: str, periodo_id: str) -> bool:
        return (
            db.scalar(
                select(func.count(Gestion.id)).where(
                    Gestion.cliente_id == cliente_id,
                    Gestion.periodo_id == periodo_id,
                )
            )
            or 0
        ) > 0

    @staticmethod
    def list_por_periodo(db: Session, periodo_id: str) -> list[Gestion]:
        return list(
            db.scalars(
                select(Gestion)
                .options(
                    joinedload(Gestion.cliente),
                    joinedload(Gestion.tipo_operacion),
                    joinedload(Gestion.operador),
                )
                .where(Gestion.periodo_id == periodo_id)
            )
        )

    @staticmethod
    def count_por_periodo(db: Session, periodo_id: str) -> int:
        return db.scalar(
            select(func.count(Gestion.id)).where(Gestion.periodo_id == periodo_id)
        ) or 0
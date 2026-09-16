from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.periodo import Periodo


class PeriodoRepo:
    @staticmethod
    def _unset_vigente(db: Session) -> None:
        db.execute(update(Periodo).values(periodo_vigente=False))

    @staticmethod
    def list(db: Session) -> list[Periodo]:
        return list(
            db.scalars(
                select(Periodo).order_by(
                    Periodo.anio.desc(), Periodo.mes.desc()
                )
            )
        )

    @staticmethod
    def get(db: Session, periodo_id: str) -> Periodo | None:
        return db.get(Periodo, periodo_id)

    @staticmethod
    def get_vigente(db: Session) -> Periodo | None:
        return db.scalar(
            select(Periodo).where(Periodo.periodo_vigente.is_(True)).limit(1)
        )

    @staticmethod
    def get_by_mes_anio(db: Session, mes: int, anio: int) -> Periodo | None:
        return db.scalar(
            select(Periodo).where(Periodo.mes == mes, Periodo.anio == anio)
        )


class TipoOperacionRepo:
    @staticmethod
    def list(db: Session) -> list:
        from app.models.catalogos import (  # local para evitar import circulares
            TipoOperacion,
        )

        return list(db.scalars(select(TipoOperacion).order_by(TipoOperacion.nombre)))

    @staticmethod
    def get(db: Session, tipo_id: str):
        from app.models.catalogos import TipoOperacion

        return db.get(TipoOperacion, tipo_id)

    @staticmethod
    def get_by_codigo(db: Session, codigo: str):
        from app.models.catalogos import TipoOperacion

        return db.scalar(
            select(TipoOperacion).where(TipoOperacion.codigo == codigo)
        )


class MotivoRepo:
    @staticmethod
    def list(db: Session) -> list:
        from app.models.catalogos import MotivoConciliacion

        return list(
            db.scalars(select(MotivoConciliacion).order_by(MotivoConciliacion.nombre))
        )

    @staticmethod
    def get(db: Session, motivo_id: str):
        from app.models.catalogos import MotivoConciliacion

        return db.get(MotivoConciliacion, motivo_id)

    @staticmethod
    def get_by_codigo(db: Session, codigo: str):
        from app.models.catalogos import MotivoConciliacion

        return db.scalar(
            select(MotivoConciliacion).where(MotivoConciliacion.codigo == codigo)
        )
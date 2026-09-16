from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.periodo import Periodo
from app.repositories.periodo_repo import PeriodoRepo
from app.schemas.periodo import PeriodoCreate, PeriodoUpdate


class PeriodoService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self) -> list[Periodo]:
        return PeriodoRepo.list(self.db)

    def get_vigente(self) -> Periodo | None:
        return PeriodoRepo.get_vigente(self.db)

    def crear(self, data: PeriodoCreate) -> Periodo:
        if PeriodoRepo.get_by_mes_anio(self.db, data.mes, data.anio):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un período para ese mes y año.",
            )
        periodo = Periodo(
            nombre=data.nombre,
            mes=data.mes,
            anio=data.anio,
            periodo_vigente=data.periodo_vigente,
        )
        self.db.add(periodo)
        if data.periodo_vigente:
            PeriodoRepo._unset_vigente(self.db)
            periodo.periodo_vigente = True
        self.db.commit()
        self.db.refresh(periodo)
        return periodo

    def actualizar(self, periodo_id: str, data: PeriodoUpdate) -> Periodo:
        periodo = PeriodoRepo.get(self.db, periodo_id)
        if periodo is None:
            raise HTTPException(status_code=404, detail="Período inexistente.")
        if data.nombre is not None:
            periodo.nombre = data.nombre
        if data.periodo_vigente is True:
            PeriodoRepo._unset_vigente(self.db)
            periodo.periodo_vigente = True
        elif data.periodo_vigente is False and periodo.periodo_vigente:
            periodo.periodo_vigente = False
        self.db.commit()
        self.db.refresh(periodo)
        return periodo
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario, require_supervisor
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.periodo import PeriodoCreate, PeriodoOut, PeriodoUpdate
from app.services.periodo_service import PeriodoService

router = APIRouter(prefix="/periodos", tags=["periodos"])


@router.get("", response_model=list[PeriodoOut])
def listar_periodos(
    _: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    return PeriodoService(db).listar()


@router.get("/vigente", response_model=PeriodoOut | None)
def periodo_vigente(
    _: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    return PeriodoService(db).get_vigente()


@router.post("", response_model=PeriodoOut, status_code=201)
def crear_periodo(
    data: PeriodoCreate,
    _: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    return PeriodoService(db).crear(data)


@router.patch("/{periodo_id}", response_model=PeriodoOut)
def actualizar_periodo(
    periodo_id: str,
    data: PeriodoUpdate,
    _: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    return PeriodoService(db).actualizar(periodo_id, data)
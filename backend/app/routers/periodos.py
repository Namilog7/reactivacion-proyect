from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario, require_supervisor
from app.database import get_db
from app.sandbox.deps import bloquear_demo, get_reader_demo
from app.sandbox.principal import Principal
from app.sandbox.reader import DemoReader
from app.schemas.periodo import PeriodoCreate, PeriodoOut, PeriodoUpdate
from app.services.periodo_service import PeriodoService

router = APIRouter(prefix="/periodos", tags=["periodos"])


@router.get("", response_model=list[PeriodoOut])
def listar_periodos(
    _: Annotated[Principal, Depends(get_current_usuario)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.periodos()
    return PeriodoService(db).listar()


@router.get("/vigente", response_model=PeriodoOut | None)
def periodo_vigente(
    _: Annotated[Principal, Depends(get_current_usuario)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.periodo_vigente()
    return PeriodoService(db).get_vigente()


@router.post("", response_model=PeriodoOut, status_code=201)
def crear_periodo(
    data: PeriodoCreate,
    _: Annotated[Principal, Depends(bloquear_demo)],
    __: Annotated[Principal, Depends(require_supervisor)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return PeriodoService(db).crear(data)


@router.patch("/{periodo_id}", response_model=PeriodoOut)
def actualizar_periodo(
    periodo_id: str,
    data: PeriodoUpdate,
    _: Annotated[Principal, Depends(bloquear_demo)],
    __: Annotated[Principal, Depends(require_supervisor)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return PeriodoService(db).actualizar(periodo_id, data)
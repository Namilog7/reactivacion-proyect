from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.database import get_db
from app.sandbox.deps import get_reader_demo
from app.sandbox.principal import Principal
from app.sandbox.reader import DemoReader
from app.repositories.periodo_repo import MotivoRepo, TipoOperacionRepo
from app.schemas.common import ORMModel
from app.schemas.gestion import TipoOperacionOut

router = APIRouter(tags=["catálogos"])


class MotivoOut(ORMModel):
    id: str
    codigo: str
    nombre: str
    descripcion: str | None


@router.get("/tipos-operacion", response_model=list[TipoOperacionOut])
def listar_tipos_operacion(
    _: Annotated[Principal, Depends(get_current_usuario)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.tipos_operacion()
    return TipoOperacionRepo.list(db)


@router.get("/motivos-conciliacion", response_model=list[MotivoOut])
def listar_motivos(
    _: Annotated[Principal, Depends(get_current_usuario)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.motivos()
    return MotivoRepo.list(db)
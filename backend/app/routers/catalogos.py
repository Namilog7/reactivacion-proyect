from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.database import get_db
from app.models.usuario import Usuario
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
    _: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    return TipoOperacionRepo.list(db)


@router.get("/motivos-conciliacion", response_model=list[MotivoOut])
def listar_motivos(
    _: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    return MotivoRepo.list(db)
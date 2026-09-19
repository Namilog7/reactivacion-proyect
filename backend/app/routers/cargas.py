from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_supervisor
from app.database import get_db
from app.domain.cargas import motivos_disponibles
from app.sandbox.deps import bloquear_demo, get_reader_demo
from app.sandbox.principal import Principal
from app.sandbox.reader import DemoReader
from app.services.carga_service import CargaService

router = APIRouter(prefix="/cargas", tags=["cargas"])


@router.get("/motivos")
def listar_motivos(_: Annotated[Principal, Depends(require_supervisor)]):
    return motivos_disponibles()


@router.get("/resumen")
def resumen_operadores(
    _: Annotated[Principal, Depends(require_supervisor)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.cargas_resumen()
    return CargaService(db).resumen_operadores()


@router.post("", status_code=201)
def cargar_archivo(
    supervisor: Annotated[Principal, Depends(require_supervisor)],
    read_only: Annotated[Principal, Depends(bloquear_demo)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile,
    operador_id: str = Form(...),
    motivo: str = Form(...),
    periodo_id: str | None = Form(default=None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Debe seleccionar un archivo.")
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400, detail="El archivo debe tener extensión .xlsx."
        )
    contenido = file.file.read()
    return CargaService(db).grabar(
        operador_id=operador_id,
        motivo=motivo,
        contenido=contenido,
        nombre_archivo=file.filename,
        periodo_id=periodo_id,
    )
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario, require_supervisor
from app.database import get_db
from app.sandbox.deps import bloquear_demo, get_reader_demo
from app.sandbox.principal import Principal
from app.sandbox.reader import DemoReader
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    _: Annotated[Principal, Depends(require_supervisor)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.usuarios()
    return UsuarioService(db).listar()


@router.post("", response_model=UsuarioOut, status_code=201)
def crear_usuario(
    data: UsuarioCreate,
    _: Annotated[Principal, Depends(bloquear_demo)],
    __: Annotated[Principal, Depends(require_supervisor)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return UsuarioService(db).crear(data)


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(
    usuario_id: str,
    data: UsuarioUpdate,
    actor: Annotated[Principal, Depends(bloquear_demo)],
    __: Annotated[Principal, Depends(require_supervisor)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return UsuarioService(db).actualizar(usuario_id, data, actor_id=str(actor.id))


@router.get("/{usuario_id}", response_model=UsuarioOut)
def consultar_usuario(
    usuario_id: str,
    _: Annotated[Principal, Depends(require_supervisor)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    if reader is not None:
        return reader.get_usuario(usuario_id)
    return UsuarioService(db).get(usuario_id)


@router.delete("/{usuario_id}", status_code=204)
def desactivar_usuario(
    usuario_id: str,
    actor: Annotated[Principal, Depends(bloquear_demo)],
    __: Annotated[Principal, Depends(require_supervisor)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """Desactiva un operador sin eliminarlo físicamente (trazabilidad)."""
    from fastapi import Response

    service = UsuarioService(db)
    usuario = service.get(usuario_id)
    if str(usuario.id) == str(actor.id):
        raise HTTPException(status_code=400, detail="No puede desactivarse a sí mismo.")
    usuario.activo = False
    db.commit()
    return Response(status_code=204)
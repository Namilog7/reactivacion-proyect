from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario, require_supervisor
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    _: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    return UsuarioService(db).listar()


@router.post("", response_model=UsuarioOut, status_code=201)
def crear_usuario(
    data: UsuarioCreate,
    _: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    return UsuarioService(db).crear(data)


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(
    usuario_id: str,
    data: UsuarioUpdate,
    actor: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    return UsuarioService(db).actualizar(usuario_id, data, actor_id=str(actor.id))


@router.get("/{usuario_id}", response_model=UsuarioOut)
def consultar_usuario(
    usuario_id: str,
    _: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    return UsuarioService(db).get(usuario_id)


@router.delete("/{usuario_id}", status_code=204)
def desactivar_usuario(
    usuario_id: str,
    actor: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
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
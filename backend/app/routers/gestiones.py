from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.common import Paginated
from app.schemas.gestion import (
    GestionCreate,
    GestionOut,
    GestionUpdate,
    HistorialOut,
)
from app.services.gestion_service import GestionService

router = APIRouter(prefix="/gestiones", tags=["gestiones"])


def _verificar_acceso(gestion, actor: Usuario):
    if actor.rol == "OPERADOR" and str(gestion.operador_id) != str(actor.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede acceder a gestiones de otros operadores.",
        )


@router.get("", response_model=Paginated[GestionOut])
def listar_gestiones(
    usuario: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
    periodo_id: str | None = None,
    operador_id: str | None = None,
    q: str | None = None,
    tipo_operacion_id: str | None = None,
    pago: bool | None = None,
    desbloqueado: bool | None = None,
    tiene_nc: bool | None = None,
    alerta: str | None = Query(default=None, pattern="^(SI|CRITICA)$"),
    sort: str = Query(default="updated_at", pattern="^(cliente_numero|fecha_ofrecida_pago|updated_at)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 20,
):
    service = GestionService(db)
    if usuario.rol == "OPERADOR":
        operador_id = None
    return service.listar(
        actor_rol=usuario.rol,
        actor_id=str(usuario.id),
        periodo_id=periodo_id,
        operador_id=operador_id if usuario.rol == "SUPERVISOR" else None,
        q=q,
        tipo_operacion_id=tipo_operacion_id,
        pago=pago,
        desbloqueado=desbloqueado,
        tiene_nc=tiene_nc,
        alerta=alerta,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=GestionOut, status_code=201)
def crear_gestion(
    data: GestionCreate,
    usuario: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    return GestionService(db).crear(
        data, actor_rol=usuario.rol, actor_id=str(usuario.id)
    )


@router.get("/{gestion_id}", response_model=GestionOut)
def obtener_gestion(
    gestion_id: str,
    usuario: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    service = GestionService(db)
    gestion = service.get(gestion_id)
    _verificar_acceso(gestion, usuario)
    return service.obtener_dto(gestion_id)


@router.patch("/{gestion_id}", response_model=GestionOut)
def actualizar_gestion(
    gestion_id: str,
    data: GestionUpdate,
    usuario: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    service = GestionService(db)
    gestion = service.get(gestion_id)
    _verificar_acceso(gestion, usuario)
    return service.actualizar(
        gestion_id, data, actor_rol=usuario.rol, actor_id=str(usuario.id)
    )


@router.get("/{gestion_id}/historial", response_model=list[HistorialOut])
def historial_gestion(
    gestion_id: str,
    usuario: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
):
    service = GestionService(db)
    gestion = service.get(gestion_id)
    _verificar_acceso(gestion, usuario)
    return service.historial(gestion_id)
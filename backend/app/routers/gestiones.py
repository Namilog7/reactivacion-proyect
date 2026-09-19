from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.database import get_db
from app.sandbox.deps import bloquear_demo, get_reader_demo
from app.sandbox.principal import Principal
from app.sandbox.reader import DemoReader
from app.schemas.common import Paginated
from app.schemas.gestion import (
    GestionCreate,
    GestionOut,
    GestionUpdate,
    HistorialOut,
)
from app.services.gestion_service import GestionService

router = APIRouter(prefix="/gestiones", tags=["gestiones"])


def _verificar_acceso(gestion, actor: Principal):
    if actor.rol != "OPERADOR":
        return
    if actor.es_demo:
        gestion_operador_id = gestion["operador"]["id"]
        actor_operador_id = actor.operador_demo_id
    else:
        gestion_operador_id = str(gestion.operador_id)
        actor_operador_id = str(actor.id)
    if gestion_operador_id != actor_operador_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede acceder a gestiones de otros operadores.",
        )


@router.get("", response_model=Paginated[GestionOut])
def listar_gestiones(
    usuario: Annotated[Principal, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
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
    if reader is not None:
        return reader.gestiones(
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
    _: Annotated[Principal, Depends(bloquear_demo)],
    usuario: Annotated[Principal, Depends(get_current_usuario)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    return GestionService(db).crear(
        data, actor_rol=usuario.rol, actor_id=str(usuario.id)
    )


@router.get("/{gestion_id}", response_model=GestionOut)
def obtener_gestion(
    gestion_id: str,
    usuario: Annotated[Principal, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
):
    if reader is not None:
        gestion = reader.get_gestion(gestion_id)
        _verificar_acceso(gestion, usuario)
        return gestion
    service = GestionService(db)
    gestion = service.get(gestion_id)
    _verificar_acceso(gestion, usuario)
    return service.obtener_dto(gestion_id)


@router.patch("/{gestion_id}", response_model=GestionOut)
def actualizar_gestion(
    gestion_id: str,
    data: GestionUpdate,
    _: Annotated[Principal, Depends(bloquear_demo)],
    usuario: Annotated[Principal, Depends(get_current_usuario)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
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
    usuario: Annotated[Principal, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
    reader: Annotated[DemoReader | None, Depends(get_reader_demo)] = None,
):
    if reader is not None:
        gestion = reader.get_gestion(gestion_id)
        _verificar_acceso(gestion, usuario)
        return reader.historial(gestion_id)
    service = GestionService(db)
    gestion = service.get(gestion_id)
    _verificar_acceso(gestion, usuario)
    return service.historial(gestion_id)
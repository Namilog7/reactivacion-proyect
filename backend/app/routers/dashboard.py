from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario, require_supervisor
from app.database import get_db
from app.domain.alertas import evaluar_alertas
from app.domain.enums import Rol
from app.models.gestion import Gestion
from app.models.periodo import Periodo
from app.models.usuario import Usuario
from app.repositories.gestion_repo import GestionRepo
from app.repositories.periodo_repo import PeriodoRepo

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/operador")
def dashboard_operador(
    usuario: Annotated[Usuario, Depends(get_current_usuario)],
    db: Annotated[Session, Depends(get_db)],
    periodo_id: str | None = None,
):
    if periodo_id:
        periodo = db.get(Periodo, periodo_id)
        if periodo is None:
            periodo = None
    else:
        periodo = PeriodoRepo.get_vigente(db)
    if periodo is None:
        return {
            "periodo_id": None,
            "periodo_nombre": None,
            "total_gestiones": 0,
            "total_pagos": 0,
            "alertas": 0,
            "criticas": 0,
            "problemas_nc": 0,
            "problemas_desbloqueo": 0,
        }

    gestiones = (
        db.scalars(
            select(Gestion)
            .options()
            .where(
                Gestion.periodo_id == periodo.id,
                Gestion.operador_id == usuario.id,
            )
        )
        .all()
    )

    total = len(gestiones)
    pagos = (
        db.scalar(
            select(func.count(Gestion.id)).where(
                Gestion.periodo_id == periodo.id,
                Gestion.operador_id == usuario.id,
                Gestion.pago.is_(True),
            )
        )
        or 0
    )
    alertas = criticas = problemas_nc = problemas_desbloqueo = 0
    for g in gestiones:
        ev = evaluar_alertas(
            g.tipo_operacion.codigo, g.pago, g.tiene_nc, g.desbloqueado
        )
        if ev["nivel"] != "NINGUNA":
            alertas += 1
        if ev["nivel"] == "CRITICA":
            criticas += 1
        if ev["nc_alerta"]:
            problemas_nc += 1
        if ev["desbloqueo_alerta"]:
            problemas_desbloqueo += 1

    return {
        "periodo_id": str(periodo.id),
        "periodo_nombre": periodo.nombre,
        "total_gestiones": total,
        "total_pagos": pagos,
        "alertas": alertas,
        "criticas": criticas,
        "problemas_nc": problemas_nc,
        "problemas_desbloqueo": problemas_desbloqueo,
    }


@router.get("/supervisor")
def dashboard_supervisor(
    _: Annotated[Usuario, Depends(require_supervisor)],
    db: Annotated[Session, Depends(get_db)],
):
    total_operadores = (
        db.scalar(select(func.count(Usuario.id)).where(Usuario.rol == Rol.OPERADOR)) or 0
    )
    operadores_activos = (
        db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.rol == Rol.OPERADOR, Usuario.activo.is_(True)
            )
        )
        or 0
    )
    total_periodos = db.scalar(select(func.count(Periodo.id))) or 0
    total_gestiones = db.scalar(select(func.count(Gestion.id))) or 0

    periodos = PeriodoRepo.list(db)
    resumen_periodos = []
    for p in periodos:
        resumen_periodos.append(
            {
                "id": str(p.id),
                "nombre": p.nombre,
                "mes": p.mes,
                "anio": p.anio,
                "periodo_vigente": p.periodo_vigente,
                "total_gestiones": GestionRepo.count_por_periodo(db, p.id),
            }
        )

    return {
        "total_operadores": total_operadores,
        "operadores_activos": operadores_activos,
        "total_periodos": total_periodos,
        "total_gestiones": total_gestiones,
        "periodos": resumen_periodos,
    }
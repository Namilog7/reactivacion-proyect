from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.domain.alertas import evaluar_alertas
from app.domain.enums import CampoCambio, OrigenCambio, OrigenGestion
from app.models.cliente import Cliente
from app.models.gestion import Gestion
from app.repositories.cliente_repo import ClienteRepo
from app.repositories.gestion_repo import GestionRepo
from app.repositories.periodo_repo import PeriodoRepo, TipoOperacionRepo
from app.schemas.gestion import GestionCreate, GestionUpdate
from app.services.historial_service import HistorialService

SORT_FIELDS = {
    "cliente_numero": "cliente_numero",
    "fecha_ofrecida_pago": "fecha_ofrecida_pago",
    "updated_at": "updated_at",
}


def to_dto(g: Gestion) -> dict:
    alertas = evaluar_alertas(
        tipo_operacion_codigo=g.tipo_operacion.codigo,
        pago=g.pago,
        tiene_nc=g.tiene_nc,
        desbloqueado=g.desbloqueado,
    )
    return {
        "id": str(g.id),
        "cliente_numero": g.cliente.numero,
        "cliente_nombre": g.cliente.nombre,
        "operador": {"id": str(g.operador.id), "nombre": g.operador.nombre},
        "periodo_id": str(g.periodo_id),
        "periodo_nombre": g.periodo.nombre,
        "tipo_operacion": {
            "id": str(g.tipo_operacion.id),
            "codigo": g.tipo_operacion.codigo,
            "nombre": g.tipo_operacion.nombre,
        },
        "fecha_ofrecida_pago": g.fecha_ofrecida_pago,
        "pago": g.pago,
        "desbloqueado": g.desbloqueado,
        "tiene_nc": g.tiene_nc,
        "observaciones": g.observaciones,
        "origen": g.origen,
        "conciliacion_origen_id": str(g.conciliacion_origen_id)
        if g.conciliacion_origen_id
        else None,
        "alertas": alertas,
        "created_at": g.created_at,
        "updated_at": g.updated_at,
    }


class GestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._historial = HistorialService(db)

    def get(self, gestion_id: str) -> Gestion:
        g = GestionRepo.get(self.db, gestion_id)
        if g is None:
            raise HTTPException(status_code=404, detail="Gestión inexistente.")
        return g

    def obtener_dto(self, gestion_id: str) -> dict:
        return to_dto(self.get(gestion_id))

    def listar(
        self,
        actor_rol: str,
        actor_id: str,
        periodo_id: str | None = None,
        operador_id: str | None = None,
        q: str | None = None,
        tipo_operacion_id: str | None = None,
        pago: bool | None = None,
        desbloqueado: bool | None = None,
        tiene_nc: bool | None = None,
        alerta: str | None = None,
        sort: str = "updated_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        stmt = (
            select(Gestion)
            .options(
                joinedload(Gestion.cliente),
                joinedload(Gestion.operador),
                joinedload(Gestion.periodo),
                joinedload(Gestion.tipo_operacion),
            )
        )

        if actor_rol == "OPERADOR":
            stmt = stmt.where(Gestion.operador_id == actor_id)
        elif operador_id:
            stmt = stmt.where(Gestion.operador_id == operador_id)

        if periodo_id:
            stmt = stmt.where(Gestion.periodo_id == periodo_id)
        if tipo_operacion_id:
            stmt = stmt.where(Gestion.tipo_operacion_id == tipo_operacion_id)
        if q:
            stmt = stmt.where(
                Gestion.cliente.has(Cliente.numero.ilike(f"%{q.strip()}%"))
            )

        if pago is not None:
            stmt = stmt.where(Gestion.pago.is_(pago))
        if desbloqueado is not None:
            stmt = stmt.where(Gestion.desbloqueado.is_(desbloqueado))
        if tiene_nc is not None:
            stmt = stmt.where(Gestion.tiene_nc.is_(tiene_nc))

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        sort_by_cliente = sort == "cliente_numero"
        if sort_by_cliente:
            stmt = stmt.join(Cliente, Gestion.cliente_id == Cliente.id)

        col = Cliente.numero if sort_by_cliente else getattr(Gestion, SORT_FIELDS[sort])
        col = col.desc() if order == "desc" else col.asc()
        stmt = stmt.order_by(col, Gestion.id)

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        items = list(
            self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size))
        )

        rows = [to_dto(g) for g in items]
        if alerta in {"SI", "CRITICA"}:
            if alerta == "CRITICA":
                rows = [r for r in rows if r["alertas"]["nivel"] == "CRITICA"]
            else:
                rows = [r for r in rows if r["alertas"]["nivel"] != "NINGUNA"]

        return {
            "items": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    def crear(
        self,
        data: GestionCreate,
        actor_rol: str,
        actor_id: str,
        origen: OrigenGestion = OrigenGestion.MANUAL,
        conciliacion_id: str | None = None,
    ) -> Gestion:
        periodo = PeriodoRepo.get(self.db, data.periodo_id)
        if periodo is None:
            raise HTTPException(status_code=400, detail="Período inexistente.")
        tipo = TipoOperacionRepo.get(self.db, data.tipo_operacion_id)
        if tipo is None:
            raise HTTPException(status_code=400, detail="Tipo de operación inexistente.")

        if actor_rol == "OPERADOR":
            operador_id = actor_id
            conciliacion_id = None
            origen = OrigenGestion.MANUAL
        else:
            if not data.operador_id:
                raise HTTPException(
                    status_code=400,
                    detail="El supervisor debe indicar el operador responsable.",
                )
            operador_id = data.operador_id

        cliente = ClienteRepo.get_or_create(
            self.db, data.cliente_numero, data.cliente_nombre
        )
        if GestionRepo.exists_cliente_periodo(self.db, cliente.id, data.periodo_id):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe una gestión para el cliente "
                    f"{data.cliente_numero} en el período {periodo.nombre}."
                ),
            )

        gestion = Gestion(
            cliente_id=cliente.id,
            operador_id=operador_id,
            periodo_id=periodo.id,
            tipo_operacion_id=tipo.id,
            fecha_ofrecida_pago=data.fecha_ofrecida_pago,
            pago=data.pago,
            desbloqueado=data.desbloqueado,
            tiene_nc=data.tiene_nc,
            observaciones=data.observaciones,
            origen=origen,
            conciliacion_origen_id=conciliacion_id,
        )
        self.db.add(gestion)
        self.db.flush()

        self._historial.registrar(
            gestion_id=gestion.id,
            campo=CampoCambio.CREACION,
            valor_anterior=None,
            valor_nuevo={},
            origen=(
                OrigenCambio.SUPERVISOR_MANUAL
                if actor_rol == "SUPERVISOR"
                else OrigenCambio.OPERADOR_MANUAL
            ),
            usuario_id=actor_id,
            conciliacion_id=conciliacion_id,
        )
        self.db.commit()
        return self.obtener_dto(gestion.id)

    def actualizar(
        self,
        gestion_id: str,
        data: GestionUpdate,
        actor_rol: str,
        actor_id: str,
    ) -> Gestion:
        gestion = self.get(gestion_id)
        origen = (
            OrigenCambio.SUPERVISOR_MANUAL
            if actor_rol == "SUPERVISOR"
            else OrigenCambio.OPERADOR_MANUAL
        )
        cambios = []

        def track(campo, antes, ahora):
            if antes != ahora:
                cambios.append(
                    (campo, {"value": antes}, {"value": ahora}, antes, ahora)
                )

        datos = data.model_dump(exclude_unset=True)

        if "tipo_operacion_id" in datos:
            nuevo = TipoOperacionRepo.get(self.db, datos["tipo_operacion_id"])
            if nuevo is None:
                raise HTTPException(status_code=400, detail="Tipo de operación inexistente.")
            track(
                CampoCambio.TIPO_OPERACION,
                gestion.tipo_operacion.codigo,
                nuevo.codigo,
            )
            gestion.tipo_operacion = nuevo

        if "fecha_ofrecida_pago" in datos:
            track(
                CampoCambio.FECHA_OFRECIDA_PAGO,
                gestion.fecha_ofrecida_pago,
                datos["fecha_ofrecida_pago"],
            )
            gestion.fecha_ofrecida_pago = datos["fecha_ofrecida_pago"]

        for campo, attr in (
            (CampoCambio.PAGO, "pago"),
            (CampoCambio.DESBLOQUEADO, "desbloqueado"),
            (CampoCambio.TIENE_NC, "tiene_nc"),
        ):
            if campo.value in datos:
                track(campo, getattr(gestion, attr), datos[campo.value])
                setattr(gestion, attr, datos[campo.value])

        if "observaciones" in datos:
            track(
                CampoCambio.OBSERVACIONES,
                gestion.observaciones,
                datos["observaciones"],
            )
            gestion.observaciones = datos["observaciones"]

        if cambios:
            self.db.flush()
            for campo, antes, ahora, _, _ in cambios:
                self._historial.registrar(
                    gestion_id=gestion.id,
                    campo=campo,
                    valor_anterior=antes,
                    valor_nuevo=ahora,
                    origen=origen,
                    usuario_id=actor_id,
                )
            self.db.commit()

        return self.obtener_dto(gestion.id)

    def historial(self, gestion_id: str) -> list:
        self.get(gestion_id)
        registros = self._historial.listar(gestion_id)
        salida = []
        for r in registros:
            salida.append(
                {
                    "id": str(r.id),
                    "usuario_nombre": r.usuario.nombre if r.usuario else None,
                    "conciliacion_id": str(r.conciliacion_id)
                    if r.conciliacion_id
                    else None,
                    "num_conciliacion": r.conciliacion.numero
                    if r.conciliacion
                    else None,
                    "campo": r.campo,
                    "valor_anterior": r.valor_anterior,
                    "valor_nuevo": r.valor_nuevo,
                    "origen": r.origen,
                    "created_at": r.created_at,
                }
            )
        return salida
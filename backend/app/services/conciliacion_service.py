"""Caso de uso: importación y ejecución de conciliaciones (Fases 6-8).

Guarda el archivo original + hash, clasifica registros (coincidencia,
cliente sin gestión, inconsistente, duplicado, inválido), toma snapshot
del estado anterior, aplica la estrategia del motivo y registra el
historial de cambios con origen CONCILIACION.
"""

import hashlib
import os
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.conciliacion_reglas import aplicar_estrategia
from app.domain.enums import (
    CampoCambio,
    CategoriaRegistro,
    EstadoConciliacion,
    OrigenCambio,
    OrigenGestion,
)
from app.importer.base import ErrorImportacion
from app.importer.xlsx_parser import XlsxParser
from app.models.conciliacion import Conciliacion, RegistroConciliacion
from app.models.gestion import Gestion
from app.repositories.cliente_repo import ClienteRepo
from app.repositories.gestion_repo import GestionRepo
from app.repositories.periodo_repo import MotivoRepo, PeriodoRepo, TipoOperacionRepo
from app.schemas.conciliacion import CrearGestionFaltanteRequest
from app.schemas.gestion import GestionCreate
from app.services.gestion_service import GestionService
from app.services.historial_service import HistorialService

CATS_APLICABLES = {
    CategoriaRegistro.COINCIDENCIA.value,
    CategoriaRegistro.INCONSISTENTE.value,
}


def conciliacion_to_dict(c: Conciliacion) -> dict:
    return {
        "id": str(c.id),
        "numero": c.numero,
        "supervisor": {"id": str(c.supervisor.id), "nombre": c.supervisor.nombre},
        "periodo_id": str(c.periodo.id),
        "periodo_nombre": c.periodo.nombre,
        "motivo": {
            "id": str(c.motivo.id),
            "codigo": c.motivo.codigo,
            "nombre": c.motivo.nombre,
            "descripcion": c.motivo.descripcion,
        },
        "estado": c.estado,
        "archivo_nombre": c.archivo_nombre,
        "archivo_hash": c.archivo_hash,
        "registros_procesados": c.registros_procesados,
        "coincidencias": c.coincidencias,
        "inconsistentes": c.inconsistentes,
        "clientes_inexistentes": c.clientes_inexistentes,
        "duplicados": c.duplicados,
        "invalidos": c.invalidos,
        "modificaciones": c.modificaciones,
        "error_mensaje": c.error_mensaje,
        "created_at": c.created_at,
    }


def registro_to_dict(r: RegistroConciliacion) -> dict:
    return {
        "id": str(r.id),
        "fila": r.fila,
        "cliente_numero": r.cliente_numero,
        "tipo_operacion_archivo": r.tipo_operacion_archivo,
        "categoria": r.categoria,
        "gestion_id": str(r.gestion_id) if r.gestion_id else None,
        "estado_anterior": r.estado_anterior,
        "estado_posterior": r.estado_posterior,
        "mensaje": r.mensaje,
    }


def snapshot(g: Gestion) -> dict:
    return {
        "pago": g.pago,
        "desbloqueado": g.desbloqueado,
        "tiene_nc": g.tiene_nc,
        "tipo_operacion_codigo": g.tipo_operacion.codigo,
        "fecha_ofrecida_pago": g.fecha_ofrecida_pago.isoformat()
        if g.fecha_ofrecida_pago
        else None,
        "observaciones": g.observaciones,
    }


class ConciliacionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.historial = HistorialService(db)

    # ---------- consultas ----------
    def listar(self, periodo_id: str | None = None, estado: str | None = None) -> dict:
        q = select(Conciliacion)
        if periodo_id:
            q = q.where(Conciliacion.periodo_id == periodo_id)
        if estado:
            q = q.where(Conciliacion.estado == estado)
        q = q.order_by(Conciliacion.created_at.desc())
        conciliaciones = self.db.scalars(q).all()
        total = self.db.scalar(
            select(func.count(Conciliacion.id)).select_from(q.subquery())
        ) or 0
        return {
            "items": [conciliacion_to_dict(c) for c in conciliaciones],
            "total": total,
        }

    def get(self, conciliacion_id: str) -> Conciliacion:
        c = self.db.get(Conciliacion, conciliacion_id)
        if c is None:
            raise HTTPException(status_code=404, detail="Conciliación inexistente.")
        return c

    def detalle(self, conciliacion_id: str, page: int = 1, page_size: int = 50) -> dict:
        c = self.get(conciliacion_id)
        q = (
            select(RegistroConciliacion)
            .where(RegistroConciliacion.conciliacion_id == c.id)
            .order_by(RegistroConciliacion.fila)
        )
        total = (
            self.db.scalar(select(func.count()).select_from(q.subquery())) or 0
        )
        page = max(page, 1)
        page_size = min(max(page_size, 1), 500)
        registros = list(
            self.db.scalars(q.offset((page - 1) * page_size).limit(page_size))
        )
        return {
            "conciliacion": conciliacion_to_dict(c),
            "items": [registro_to_dict(r) for r in registros],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    # ---------- creación / previsualización (Fase 6) ----------
    def crear(
        self,
        supervisor_id: str,
        periodo_id: str,
        motivo_id: str,
        contenido: bytes,
        nombre_archivo: str,
    ) -> Conciliacion:
        periodo = PeriodoRepo.get(self.db, periodo_id)
        if periodo is None:
            raise HTTPException(status_code=400, detail="Período inexistente.")
        motivo = MotivoRepo.get(self.db, motivo_id)
        if motivo is None:
            raise HTTPException(status_code=400, detail="Motivo de conciliación inexistente.")

        tipos = TipoOperacionRepo.list(self.db)
        tipos_validos = {t.codigo: {"nombre": t.nombre} for t in tipos}
        try:
            filas = XlsxParser().parse(contenido, tipos_validos)
        except ErrorImportacion as e:
            raise HTTPException(status_code=400, detail=e.mensaje)

        archivo_hash = hashlib.sha256(contenido).hexdigest()

        conc = Conciliacion(
            supervisor_id=supervisor_id,
            periodo_id=periodo.id,
            motivo_id=motivo.id,
            estado=EstadoConciliacion.PREVISUALIZACION,
            archivo_nombre=nombre_archivo,
            archivo_ruta="",  # se fija luego de persistir el id
            archivo_hash=archivo_hash,
        )
        self.db.add(conc)
        self.db.flush()

        ruta = Path(settings.upload_dir) / f"{conc.id}.xlsx"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(contenido)
        conc.archivo_ruta = str(ruta)
        registros = []
        for f in filas:
            reg = RegistroConciliacion(
                conciliacion_id=conc.id,
                fila=f.fila,
                cliente_numero=f.cliente_numero,
                tipo_operacion_archivo=f.tipo_archivo,
                tipo_operacion_id=None,
                categoria=f.categoria or "",
                mensaje=f.mensaje,
            )
            if f.tipo_codigo:
                t = TipoOperacionRepo.get_by_codigo(self.db, f.tipo_codigo)
                if t:
                    reg.tipo_operacion_id = t.id
            registros.append(reg)
        self.db.add_all(registros)
        self.db.flush()

        self._recategorizar(periodo_id, registros)
        self.db.flush()
        self._recalcular(conc)
        self.db.commit()
        return self.get(conc.id)

    # ---------- confirmación / ejecución (Fase 7) ----------
    def confirmar(self, conciliacion_id: str, supervisor_id: str) -> dict:
        conc = self.get(conciliacion_id)
        if conc.estado != EstadoConciliacion.PREVISUALIZACION:
            raise HTTPException(
                status_code=400,
                detail="La conciliación ya fue procesada o no admite confirmación.",
            )
        conc.estado = EstadoConciliacion.PROCESANDO
        self.db.flush()

        try:
            registros = list(
                self.db.scalars(
                    select(RegistroConciliacion)
                    .where(RegistroConciliacion.conciliacion_id == conc.id)
                    .order_by(RegistroConciliacion.fila)
                )
            )
            self._recategorizar(conc.periodo_id, registros)

            modificaciones = 0
            for reg in registros:
                if reg.categoria not in CATS_APLICABLES or not reg.gestion_id:
                    continue
                gestion = self.db.get(Gestion, reg.gestion_id)
                if gestion is None:
                    continue
                cambios = aplicar_estrategia(conc.motivo.codigo, gestion)
                if not cambios:
                    continue
                anterior = snapshot(gestion)
                for cambio in cambios:
                    setattr(gestion, cambio.campo.value, cambio.valor_nuevo)
                modificaciones += len(cambios)
                self.db.flush()
                posterior = snapshot(gestion)
                reg.estado_anterior = anterior
                reg.estado_posterior = posterior
                for cambio in cambios:
                    self.historial.registrar(
                        gestion_id=gestion.id,
                        campo=cambio.campo,
                        valor_anterior={"value": anterior.get(cambio.campo.value)},
                        valor_nuevo={"value": cambio.valor_nuevo},
                        origen=OrigenCambio.CONCILIACION,
                        usuario_id=supervisor_id,
                        conciliacion_id=conc.id,
                    )

            self.db.flush()
            self._recalcular(conc)
            conc.modificaciones = modificaciones
            conc.estado = EstadoConciliacion.COMPLETADA
            self.db.commit()
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            conc.estado = EstadoConciliacion.ERROR
            conc.error_mensaje = str(e)[:2000]
            self.db.commit()
            raise HTTPException(
                status_code=500,
                detail=f"La conciliación falló y fue marcada como ERROR: {e}",
            )

        return {
            "conciliacion": conciliacion_to_dict(conc),
            "coincidencias": conc.coincidencias,
            "clientes_inexistentes": conc.clientes_inexistentes,
            "modificaciones": conc.modificaciones,
        }

    # ---------- cliente sin gestión (Fase 7/§10) ----------
    def crear_gestion_faltante(
        self, conciliacion_id: str, supervisor_id: str, request: CrearGestionFaltanteRequest
    ) -> Gestion:
        conc = self.get(conciliacion_id)
        reg = self.db.get(RegistroConciliacion, request.registro_id)
        if reg is None or reg.conciliacion_id != conc.id:
            raise HTTPException(
                status_code=400, detail="El registro no pertenece a esta conciliación."
            )
        if reg.categoria != CategoriaRegistro.CLIENTE_SIN_GESTION.value:
            raise HTTPException(
                status_code=400,
                detail="Solo pueden crearse gestiones faltantes para clientes sin gestión.",
            )
        if reg.tipo_operacion_id is None or not reg.cliente_numero:
            raise HTTPException(
                status_code=400,
                detail="El registro no tiene datos suficientes (tipo de operación o cliente).",
            )

        data = GestionCreate(
            cliente_numero=reg.cliente_numero,
            cliente_nombre=request.cliente_nombre,
            periodo_id=str(conc.periodo_id),
            tipo_operacion_id=str(reg.tipo_operacion_id),
            operador_id=request.operador_id,
            fecha_ofrecida_pago=request.fecha_ofrecida_pago,
            pago=request.pago,
            desbloqueado=request.desbloqueado,
            tiene_nc=request.tiene_nc,
            observaciones=request.observaciones,
        )
        return GestionService(self.db).crear(
            data,
            actor_rol="SUPERVISOR",
            actor_id=str(supervisor_id),
            origen=OrigenGestion.CONCILIACION,
            conciliacion_id=str(conc.id),
        )

    # ---------- internos ----------
    def _recategorizar(self, periodo_id: str, registros: list[RegistroConciliacion]) -> None:
        """Clasifica cada registro contra el estado actual de las gestiones."""
        for reg in registros:
            if reg.categoria in {
                CategoriaRegistro.DUPLICADO.value,
                CategoriaRegistro.INVALIDO.value,
            }:
                continue
            cliente = ClienteRepo.get_by_numero(self.db, reg.cliente_numero) if reg.cliente_numero else None
            if cliente is None:
                reg.categoria = CategoriaRegistro.CLIENTE_SIN_GESTION.value
                reg.mensaje = (
                    "Cliente encontrado en conciliación pero sin gestión existente."
                )
                continue
            gestion = GestionRepo.get_by_cliente_periodo(self.db, cliente.id, periodo_id)
            if gestion is None:
                reg.categoria = CategoriaRegistro.CLIENTE_SIN_GESTION.value
                reg.mensaje = (
                    "Cliente encontrado en conciliación pero sin gestión existente."
                )
                reg.gestion_id = None
                continue
            if (
                reg.tipo_operacion_id
                and gestion.tipo_operacion_id != reg.tipo_operacion_id
            ):
                reg.categoria = CategoriaRegistro.INCONSISTENTE.value
                reg.mensaje = (
                    "El tipo de operación del archivo difiere de la gestión registrada."
                )
                reg.gestion_id = gestion.id
                continue
            reg.categoria = CategoriaRegistro.COINCIDENCIA.value
            reg.mensaje = None
            reg.gestion_id = gestion.id

    def _recalcular(self, conc: Conciliacion) -> None:
        base = select(func.count(RegistroConciliacion.id)).where(
            RegistroConciliacion.conciliacion_id == conc.id
        )

        def contar(categoria: str) -> int:
            return self.db.scalar(select(func.count(1)).where(
                RegistroConciliacion.conciliacion_id == conc.id,
                RegistroConciliacion.categoria == categoria,
            )) or 0

        conc.registros_procesados = self.db.scalar(base) or 0
        conc.coincidencias = contar(CategoriaRegistro.COINCIDENCIA.value)
        conc.inconsistentes = contar(CategoriaRegistro.INCONSISTENTE.value)
        conc.clientes_inexistentes = contar(CategoriaRegistro.CLIENTE_SIN_GESTION.value)
        conc.duplicados = contar(CategoriaRegistro.DUPLICADO.value)
        conc.invalidos = contar(CategoriaRegistro.INVALIDO.value)
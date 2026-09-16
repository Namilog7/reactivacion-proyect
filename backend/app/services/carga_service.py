"""Caso de uso: carga de archivos .xlsx por operador.

El supervisor sube un archivo por operador con un motivo; el sistema
actualiza las gestiones de ese operador en el período (vigente por
defecto). No se persiste auditoría ni historial de la carga.
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.alertas import evaluar_alertas
from app.domain.cargas import MOTIVOS_CARGA, aplicar_motivo, validar_motivo
from app.domain.enums import Rol
from app.importer.base import ErrorImportacion
from app.importer.clientes_parser import parse_clientes
from app.models.gestion import Gestion
from app.models.usuario import Usuario
from app.repositories.cliente_repo import ClienteRepo
from app.repositories.periodo_repo import PeriodoRepo


class CargaService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def grabar(
        self,
        *,
        operador_id: str,
        motivo: str,
        contenido: bytes,
        nombre_archivo: str,
        periodo_id: str | None = None,
    ) -> dict:
        operador = self.db.get(Usuario, operador_id)
        if operador is None or operador.rol != Rol.OPERADOR:
            raise HTTPException(status_code=400, detail="El operador indicado no existe.")
        try:
            validar_motivo(motivo)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if periodo_id:
            periodo = PeriodoRepo.get(self.db, periodo_id)
            if periodo is None:
                raise HTTPException(status_code=400, detail="Período inexistente.")
        else:
            periodo = PeriodoRepo.get_vigente(self.db)
        if periodo is None:
            raise HTTPException(
                status_code=400, detail="No hay período vigente para aplicar la carga."
            )

        try:
            archivo = parse_clientes(contenido)
        except ErrorImportacion as e:
            raise HTTPException(status_code=400, detail=e.mensaje)

        sin_gestion = actualizadas = sin_cambios = modificaciones = 0

        for numero in archivo.clientes:
            cliente = ClienteRepo.get_by_numero(self.db, numero)
            if cliente is None:
                sin_gestion += 1
                continue
            gestion = self.db.scalar(
                select(Gestion).where(
                    Gestion.cliente_id == cliente.id,
                    Gestion.periodo_id == periodo.id,
                    Gestion.operador_id == operador.id,
                )
            )
            if gestion is None:
                sin_gestion += 1
                continue
            cambios = aplicar_motivo(motivo, gestion)
            if not cambios:
                sin_cambios += 1
                continue
            for cambio in cambios:
                setattr(gestion, cambio.campo.value, cambio.valor_nuevo)
            modificaciones += len(cambios)
            actualizadas += 1

        self.db.commit()

        return {
            "operador": {"id": str(operador.id), "nombre": operador.nombre},
            "periodo": {"id": str(periodo.id), "nombre": periodo.nombre},
            "motivo": {"codigo": motivo, "nombre": MOTIVOS_CARGA[motivo]["nombre"]},
            "archivo_nombre": nombre_archivo,
            "total_filas": archivo.total_filas,
            "duplicados_archivo": archivo.duplicados,
            "invalidas_archivo": archivo.invalidas,
            "procesadas": actualizadas + sin_cambios,
            "actualizadas": actualizadas,
            "sin_cambios": sin_cambios,
            "sin_gestion": sin_gestion,
            "modificaciones": modificaciones,
        }

    def resumen_operadores(self) -> dict:
        """Estado por operador en el período vigente (para el mapa del supervisor)."""
        periodo = PeriodoRepo.get_vigente(self.db)
        items = []
        operadores = list(
            self.db.scalars(
                select(Usuario)
                .where(Usuario.rol == Rol.OPERADOR)
                .order_by(Usuario.nombre)
            )
        )
        for u in operadores:
            estado = {
                "id": str(u.id),
                "username": u.username,
                "nombre": u.nombre,
                "activo": u.activo,
                "gestiones": 0,
                "pagos": 0,
                "alertas": 0,
                "criticas": 0,
            }
            if periodo:
                gestiones = list(
                    self.db.scalars(
                        select(Gestion).where(
                            Gestion.periodo_id == periodo.id,
                            Gestion.operador_id == u.id,
                        )
                    )
                )
                estado["gestiones"] = len(gestiones)
                estado["pagos"] = sum(1 for g in gestiones if g.pago)
                for g in gestiones:
                    ev = evaluar_alertas(
                        g.tipo_operacion.codigo, g.pago, g.tiene_nc, g.desbloqueado
                    )
                    if ev["nivel"] != "NINGUNA":
                        estado["alertas"] += 1
                    if ev["nivel"] == "CRITICA":
                        estado["criticas"] += 1
            items.append(estado)

        return {
            "periodo": {"id": str(periodo.id), "nombre": periodo.nombre} if periodo else None,
            "items": items,
        }
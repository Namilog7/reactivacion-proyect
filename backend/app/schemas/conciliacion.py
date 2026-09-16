from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.enums import EstadoConciliacion
from app.schemas.common import ORMModel
from app.schemas.gestion import OperadorRef, GestionOut


class MotivoRef(ORMModel):
    id: str
    codigo: str
    nombre: str
    descripcion: str | None


class ConciliacionOut(ORMModel):
    id: str
    numero: int
    supervisor: OperadorRef
    periodo_id: str
    periodo_nombre: str
    motivo: MotivoRef
    estado: EstadoConciliacion
    archivo_nombre: str
    archivo_hash: str
    registros_procesados: int
    coincidencias: int
    inconsistentes: int
    clientes_inexistentes: int
    duplicados: int
    invalidos: int
    modificaciones: int
    error_mensaje: str | None
    created_at: datetime


class RegistroOut(ORMModel):
    id: str
    fila: int
    cliente_numero: str | None
    tipo_operacion_archivo: str | None
    categoria: str
    gestion_id: str | None
    estado_anterior: dict | None
    estado_posterior: dict | None
    mensaje: str | None


class ConciliacionListaOut(BaseModel):
    items: list[ConciliacionOut]
    total: int


class ConciliacionDetalleOut(BaseModel):
    conciliacion: ConciliacionOut
    items: list[RegistroOut]
    total: int
    page: int
    page_size: int
    pages: int


class ConfirmarSummaryOut(BaseModel):
    conciliacion: ConciliacionOut
    coincidencias: int
    clientes_inexistentes: int
    modificaciones: int


class CrearGestionFaltanteRequest(BaseModel):
    registro_id: str
    operador_id: str
    cliente_nombre: str | None = Field(default=None, max_length=200)
    fecha_ofrecida_pago: date | None = None
    pago: bool = False
    desbloqueado: bool = False
    tiene_nc: bool = False
    observaciones: str = ""
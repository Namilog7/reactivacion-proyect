from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.alertas import EvaluacionAlertas
from app.domain.enums import NivelAlerta, OrigenGestion
from app.schemas.common import ORMModel


class TipoOperacionOut(ORMModel):
    id: str
    codigo: str
    nombre: str


class OperadorRef(ORMModel):
    id: str
    nombre: str


class GestionCreate(BaseModel):
    cliente_numero: str = Field(min_length=1, max_length=30)
    cliente_nombre: str | None = Field(default=None, max_length=200)
    periodo_id: str
    tipo_operacion_id: str
    operador_id: str | None = None  # solo lo fija el supervisor
    fecha_ofrecida_pago: date | None = None
    pago: bool = False
    desbloqueado: bool = False
    tiene_nc: bool = False
    observaciones: str = ""


class GestionCreateDesdeConciliacion(GestionCreate):
    conciliacion_id: str
    registro_id: str | None = None


class GestionUpdate(BaseModel):
    tipo_operacion_id: str | None = None
    fecha_ofrecida_pago: date | None = None
    pago: bool | None = None
    desbloqueado: bool | None = None
    tiene_nc: bool | None = None
    observaciones: str | None = None


class GestionOut(ORMModel):
    id: str
    cliente_numero: str
    cliente_nombre: str | None
    operador: OperadorRef
    periodo_id: str
    periodo_nombre: str
    tipo_operacion: TipoOperacionOut
    fecha_ofrecida_pago: date | None
    pago: bool
    desbloqueado: bool
    tiene_nc: bool
    observaciones: str
    origen: OrigenGestion
    conciliacion_origen_id: str | None
    alertas: EvaluacionAlertas | None = None
    created_at: datetime
    updated_at: datetime


class HistorialOut(ORMModel):
    id: str
    usuario_nombre: str | None
    conciliacion_id: str | None
    num_conciliacion: int | None
    campo: str
    valor_anterior: dict | None
    valor_nuevo: dict
    origen: str
    created_at: datetime
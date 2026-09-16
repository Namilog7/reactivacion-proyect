from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PeriodoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    mes: int = Field(ge=1, le=12)
    anio: int = Field(ge=2000, le=2100)
    periodo_vigente: bool = False


class PeriodoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    periodo_vigente: bool | None = None


class PeriodoOut(ORMModel):
    id: str
    nombre: str
    mes: int
    anio: int
    periodo_vigente: bool
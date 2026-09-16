from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import Rol
from app.schemas.common import ORMModel


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    nombre: str = Field(min_length=1, max_length=100)
    rol: Rol = Rol.OPERADOR


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    rol: Rol | None = None
    activo: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UsuarioOut(ORMModel):
    id: str
    username: str
    nombre: str
    rol: Rol
    activo: bool
    created_at: datetime
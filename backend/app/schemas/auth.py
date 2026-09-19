from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import Rol
from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UsuarioOut(ORMModel):
    id: str
    username: str
    nombre: str
    rol: Rol
    activo: bool
    created_at: datetime
    tipo: str = "REAL"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
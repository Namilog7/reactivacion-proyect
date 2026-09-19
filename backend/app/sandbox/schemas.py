"""Schemas del modo demo/sandbox."""

from pydantic import BaseModel

from app.domain.enums import Rol


class DemoLoginRequest(BaseModel):
    rol: Rol
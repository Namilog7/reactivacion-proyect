"""Identidad del usuario que ejecuta una request.

Reemplaza al objeto SQLAlchemy `Usuario` en las dependencias de
autenticación. Cubre tanto usuarios reales (PostgreSQL) como sesiones
de demostración (Redis), manteniendo un único contrato para el resto
del código.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

TIPO_REAL = "REAL"
TIPO_DEMO = "DEMO"


@dataclass
class Principal:
    tipo: str
    rol: str
    user_id: str
    sandbox_id: str | None
    nombre: str
    username: str
    operador_demo_id: str | None = None
    activo: bool = True
    created_at: datetime | None = None

    @property
    def id(self) -> str:
        return self.user_id

    @property
    def es_demo(self) -> bool:
        return self.tipo == TIPO_DEMO


def principal_a_usuario(principal: Principal) -> dict:
    """Convierte un Principal a la forma de `UsuarioOut` (usado en /auth/me)."""
    return {
        "id": principal.user_id,
        "username": principal.username,
        "nombre": principal.nombre,
        "rol": principal.rol,
        "activo": principal.activo,
        "created_at": principal.created_at or datetime.now(timezone.utc),
        "tipo": principal.tipo,
    }
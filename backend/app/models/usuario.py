from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import Rol
from app.models.base import Base, TimestampMixin, UUIDMixin


class Usuario(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "usuarios"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[Rol] = mapped_column(
        Enum(Rol, name="rol_enum"), nullable=False, default=Rol.OPERADOR
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
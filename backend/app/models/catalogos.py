from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class TipoOperacion(Base, UUIDMixin):
    __tablename__ = "tipos_operacion"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TipoOperacion {self.codigo}>"


class MotivoConciliacion(Base, UUIDMixin):
    __tablename__ = "motivos_conciliacion"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MotivoConciliacion {self.codigo}>"
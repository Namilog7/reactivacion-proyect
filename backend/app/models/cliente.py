from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Cliente(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clientes"

    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
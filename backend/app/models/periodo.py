from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Periodo(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "periodos"
    __table_args__ = (
        UniqueConstraint("mes", "anio", name="uq_periodo_mes_anio"),
        CheckConstraint("anio >= 2000", name="ck_periodo_anio"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_periodo_mes"),
        Index(
            "uq_periodo_vigente_unico",
            "periodo_vigente",
            unique=True,
            postgresql_where="periodo_vigente = true",
        ),
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo_vigente: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
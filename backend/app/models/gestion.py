import uuid

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import OrigenGestion
from app.models.base import Base, TimestampMixin, UUIDMixin


class Gestion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "gestiones"
    __table_args__ = (
        UniqueConstraint(
            "cliente_id", "periodo_id", name="uq_gestion_cliente_periodo"
        ),
        Index("ix_gestiones_periodo", "periodo_id"),
        Index("ix_gestiones_periodo_operador", "periodo_id", "operador_id"),
        Index("ix_gestiones_cliente", "cliente_id"),
    )

    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False
    )
    operador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    periodo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("periodos.id"), nullable=False
    )
    tipo_operacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tipos_operacion.id"), nullable=False
    )
    fecha_ofrecida_pago: Mapped[Date | None] = mapped_column(Date, nullable=True)
    pago: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    desbloqueado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tiene_nc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    origen: Mapped[OrigenGestion] = mapped_column(
        Enum(OrigenGestion, name="origen_gestion_enum"),
        nullable=False,
        default=OrigenGestion.MANUAL,
    )
    conciliacion_origen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conciliaciones.id"),
        nullable=True,
    )

    cliente = relationship("Cliente", lazy="joined")
    operador = relationship("Usuario", lazy="joined")
    periodo = relationship("Periodo", lazy="joined")
    tipo_operacion = relationship("TipoOperacion", lazy="joined")
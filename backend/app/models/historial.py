import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class HistorialCambio(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "historial_cambios"
    __table_args__ = (
        Index("ix_historial_gestion", "gestion_id"),
        Index("ix_historial_conciliacion", "conciliacion_id"),
    )

    gestion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gestiones.id"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    conciliacion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conciliaciones.id"), nullable=True
    )
    campo: Mapped[str] = mapped_column(
        ENUM(
            "creacion",
            "operador",
            "tipo_operacion",
            "fecha_ofrecida_pago",
            "pago",
            "desbloqueado",
            "tiene_nc",
            "observaciones",
            name="campo_cambio_enum",
            create_type=False,
        ),
        nullable=False,
    )
    valor_anterior: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    valor_nuevo: Mapped[dict] = mapped_column(JSONB, nullable=False)
    origen: Mapped[str] = mapped_column(
        ENUM(
            "OPERADOR_MANUAL",
            "SUPERVISOR_MANUAL",
            "CONCILIACION",
            name="origen_cambio_enum",
            create_type=False,
        ),
        nullable=False,
    )

    usuario = relationship("Usuario", lazy="joined")
    conciliacion = relationship("Conciliacion", lazy="joined")
    gestion = relationship("Gestion", lazy="joined")
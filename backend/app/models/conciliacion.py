import uuid

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import EstadoConciliacion
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.periodo import Periodo


class Conciliacion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conciliaciones"
    __table_args__ = (Index("ix_conciliaciones_periodo", "periodo_id"),)

    numero: Mapped[int] = mapped_column(Integer, Identity(), unique=True, nullable=False)
    supervisor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    periodo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("periodos.id"), nullable=False
    )
    motivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("motivos_conciliacion.id"), nullable=False
    )
    estado: Mapped[EstadoConciliacion] = mapped_column(
        Enum(EstadoConciliacion, name="estado_conciliacion_enum"),
        nullable=False,
        default=EstadoConciliacion.PREVISUALIZACION,
    )
    archivo_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    archivo_ruta: Mapped[str] = mapped_column(String(500), nullable=False)
    archivo_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    registros_procesados: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    coincidencias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inconsistentes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clientes_inexistentes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    duplicados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    modificaciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)

    supervisor = relationship("Usuario", lazy="joined")
    periodo: Mapped[Periodo] = relationship("Periodo", lazy="joined")
    motivo = relationship("MotivoConciliacion", lazy="joined")
    registros = relationship(
        "RegistroConciliacion",
        back_populates="conciliacion",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="RegistroConciliacion.fila",
    )


class RegistroConciliacion(Base, UUIDMixin):
    __tablename__ = "registros_conciliacion"
    __table_args__ = (
        Index("ix_registros_conciliacion_conciliacion", "conciliacion_id"),
    )

    conciliacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conciliaciones.id"), nullable=False
    )
    fila: Mapped[int] = mapped_column(Integer, nullable=False)
    cliente_numero: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tipo_operacion_archivo: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    tipo_operacion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tipos_operacion.id"), nullable=True
    )
    categoria: Mapped[str] = mapped_column(String(30), nullable=False)
    gestion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gestiones.id"), nullable=True
    )
    estado_anterior: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estado_posterior: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)

    conciliacion = relationship("Conciliacion", back_populates="registros")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Registro {self.fila} {self.categoria}>"
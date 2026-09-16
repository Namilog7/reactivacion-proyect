"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enums() -> None:
    rol_enum = postgresql.ENUM("SUPERVISOR", "OPERADOR", name="rol_enum")
    rol_enum.create(op.get_bind(), checkfirst=True)

    postgresql.ENUM("MANUAL", "CONCILIACION", name="origen_gestion_enum").create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "PREVISUALIZACION", "PROCESANDO", "COMPLETADA", "ERROR",
        name="estado_conciliacion_enum",
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "creacion", "operador", "tipo_operacion", "fecha_ofrecida_pago",
        "pago", "desbloqueado", "tiene_nc", "observaciones",
        name="campo_cambio_enum",
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "OPERADOR_MANUAL", "SUPERVISOR_MANUAL", "CONCILIACION",
        name="origen_cambio_enum",
    ).create(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    _create_enums()
    bind = op.get_bind()
    uuid_pk = sa.Column(
        "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )
    ts = lambda name: sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    op.create_table(
        "usuarios",
        uuid_pk,
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("rol", postgresql.ENUM(name="rol_enum", create_type=False), nullable=False, server_default="OPERADOR"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        ts("created_at"),
        ts("updated_at"),
        sa.UniqueConstraint("username", name="uq_usuarios_username"),
    )

    op.create_table(
        "clientes",
        uuid_pk,
        sa.Column("numero", sa.String(30), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=True),
        ts("created_at"),
        ts("updated_at"),
        sa.UniqueConstraint("numero", name="uq_clientes_numero"),
    )

    op.create_table(
        "periodos",
        uuid_pk,
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("periodo_vigente", sa.Boolean(), nullable=False, server_default=sa.false()),
        ts("created_at"),
        ts("updated_at"),
        sa.CheckConstraint("anio >= 2000", name="ck_periodo_anio"),
        sa.CheckConstraint("mes BETWEEN 1 AND 12", name="ck_periodo_mes"),
        sa.UniqueConstraint("mes", "anio", name="uq_periodo_mes_anio"),
    )
    op.create_index(
        "uq_periodo_vigente_unico", "periodos", ["periodo_vigente"],
        unique=True, postgresql_where=sa.text("periodo_vigente = true"),
    )

    op.create_table(
        "tipos_operacion",
        uuid_pk,
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.UniqueConstraint("codigo", name="uq_tipos_operacion_codigo"),
    )

    op.create_table(
        "motivos_conciliacion",
        uuid_pk,
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.UniqueConstraint("codigo", name="uq_motivos_conciliacion_codigo"),
    )

    op.create_table(
        "conciliaciones",
        uuid_pk,
        sa.Column("numero", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("supervisor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("periodo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("periodos.id"), nullable=False),
        sa.Column("motivo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("motivos_conciliacion.id"), nullable=False),
        sa.Column("estado", postgresql.ENUM(name="estado_conciliacion_enum", create_type=False), nullable=False, server_default="PREVISUALIZACION"),
        sa.Column("archivo_nombre", sa.String(255), nullable=False),
        sa.Column("archivo_ruta", sa.String(500), nullable=False),
        sa.Column("archivo_hash", sa.String(64), nullable=False),
        sa.Column("registros_procesados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("coincidencias", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inconsistentes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clientes_inexistentes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("modificaciones", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_mensaje", sa.Text(), nullable=True),
        ts("created_at"),
        ts("updated_at"),
        sa.UniqueConstraint("numero", name="uq_conciliaciones_numero"),
    )
    op.create_index("ix_conciliaciones_periodo", "conciliaciones", ["periodo_id"])

    op.create_table(
        "gestiones",
        uuid_pk,
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("operador_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("periodo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("periodos.id"), nullable=False),
        sa.Column("tipo_operacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tipos_operacion.id"), nullable=False),
        sa.Column("fecha_ofrecida_pago", sa.Date(), nullable=True),
        sa.Column("pago", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("desbloqueado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tiene_nc", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("observaciones", sa.Text(), nullable=False, server_default=""),
        sa.Column("origen", postgresql.ENUM(name="origen_gestion_enum", create_type=False), nullable=False, server_default="MANUAL"),
        sa.Column("conciliacion_origen_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conciliaciones.id"), nullable=True),
        ts("created_at"),
        ts("updated_at"),
        sa.UniqueConstraint("cliente_id", "periodo_id", name="uq_gestion_cliente_periodo"),
    )
    op.create_index("ix_gestiones_periodo", "gestiones", ["periodo_id"])
    op.create_index("ix_gestiones_periodo_operador", "gestiones", ["periodo_id", "operador_id"])
    op.create_index("ix_gestiones_cliente", "gestiones", ["cliente_id"])

    op.create_table(
        "registros_conciliacion",
        uuid_pk,
        sa.Column("conciliacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conciliaciones.id"), nullable=False),
        sa.Column("fila", sa.Integer(), nullable=False),
        sa.Column("cliente_numero", sa.String(30), nullable=True),
        sa.Column("tipo_operacion_archivo", sa.String(100), nullable=True),
        sa.Column("tipo_operacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tipos_operacion.id"), nullable=True),
        sa.Column("categoria", sa.String(30), nullable=False),
        sa.Column("gestion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gestiones.id"), nullable=True),
        sa.Column("estado_anterior", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("estado_posterior", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("mensaje", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_registros_conciliacion_conciliacion",
        "registros_conciliacion", ["conciliacion_id"],
    )

    op.create_table(
        "historial_cambios",
        uuid_pk,
        sa.Column("gestion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gestiones.id"), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("conciliacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conciliaciones.id"), nullable=True),
        sa.Column("campo", postgresql.ENUM(name="campo_cambio_enum", create_type=False), nullable=False),
        sa.Column("valor_anterior", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("valor_nuevo", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("origen", postgresql.ENUM(name="origen_cambio_enum", create_type=False), nullable=False),
        ts("created_at"),
        ts("updated_at"),
    )
    op.create_index("ix_historial_gestion", "historial_cambios", ["gestion_id"])
    op.create_index("ix_historial_conciliacion", "historial_cambios", ["conciliacion_id"])


def downgrade() -> None:
    op.drop_table("historial_cambios")
    op.drop_table("registros_conciliacion")
    op.drop_table("gestiones")
    op.drop_table("conciliaciones")
    op.drop_table("motivos_conciliacion")
    op.drop_table("tipos_operacion")
    op.drop_table("periodos")
    op.drop_table("clientes")
    op.drop_table("usuarios")

    for enum in ("origen_cambio_enum", "campo_cambio_enum",
                 "estado_conciliacion_enum", "origen_gestion_enum", "rol_enum"):
        postgresql.ENUM(name=enum).drop(op.get_bind(), checkfirst=True)
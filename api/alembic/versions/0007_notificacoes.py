"""dispositivo, notificacao e envio_push

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dispositivo",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("plataforma", sa.String(10), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deletado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dispositivo_usuario_id", "dispositivo", ["usuario_id"])
    op.create_table(
        "notificacao",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("referencia_id", sa.Integer(), nullable=False),
        sa.Column("enviar_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tentativas", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deletado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_notificacao_pendente",
        "notificacao",
        ["enviar_em"],
        postgresql_where=sa.text("processada_em IS NULL"),
    )
    op.create_table(
        "envio_push",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "notificacao_id",
            sa.Integer(),
            sa.ForeignKey("notificacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dispositivo_id",
            sa.Integer(),
            sa.ForeignKey("dispositivo.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticket_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("erro", sa.String(100), nullable=True),
        sa.Column("verificado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deletado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_envio_push_notificacao_id", "envio_push", ["notificacao_id"])
    op.create_index("ix_envio_push_dispositivo_id", "envio_push", ["dispositivo_id"])
    op.create_index(
        "ix_envio_push_aguardando_recibo",
        "envio_push",
        ["criado_em"],
        postgresql_where=sa.text("status = 'enviado'"),
    )


def downgrade() -> None:
    op.drop_index("ix_envio_push_aguardando_recibo", table_name="envio_push")
    op.drop_index("ix_envio_push_dispositivo_id", table_name="envio_push")
    op.drop_index("ix_envio_push_notificacao_id", table_name="envio_push")
    op.drop_table("envio_push")
    op.drop_index("ix_notificacao_pendente", table_name="notificacao")
    op.drop_table("notificacao")
    op.drop_index("ix_dispositivo_usuario_id", table_name="dispositivo")
    op.drop_table("dispositivo")

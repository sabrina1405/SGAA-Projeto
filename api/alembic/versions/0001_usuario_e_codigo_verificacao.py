"""usuario e codigo_verificacao

Revision ID: 0001
Revises:
Create Date: 2026-10-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("nome_completo", sa.String(100), nullable=False),
        sa.Column("email", sa.String(80), nullable=False, unique=True),
        sa.Column("senha", sa.String(150), nullable=True),
        sa.Column(
            "tipo",
            sa.Enum("professor", "aluno", name="tipo_usuario_enum"),
            nullable=False,
        ),
        sa.Column("versao_token", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tentativas_login", sa.Integer(), server_default="0", nullable=False),
        sa.Column("bloqueado_ate", sa.DateTime(timezone=True), nullable=True),
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
    op.create_table(
        "codigo_verificacao",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("codigo_hash", sa.String(64), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tentativas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("usado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_codigo_verificacao_usuario_id", "codigo_verificacao", ["usuario_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_codigo_verificacao_usuario_id", table_name="codigo_verificacao")
    op.drop_table("codigo_verificacao")
    op.drop_table("usuario")
    sa.Enum(name="tipo_usuario_enum").drop(op.get_bind())

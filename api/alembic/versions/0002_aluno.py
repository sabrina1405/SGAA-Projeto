"""aluno

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "aluno",
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("data_nascimento", sa.Date(), nullable=False),
        sa.Column("possui_responsavel", sa.Boolean(), nullable=False),
        sa.Column("cpf", sa.String(11), nullable=True, unique=True),
        sa.Column("telefone", sa.String(11), nullable=True),
        sa.Column("responsavel_nome", sa.String(100), nullable=True),
        sa.Column("responsavel_cpf", sa.String(11), nullable=True),
        sa.Column("responsavel_telefone", sa.String(11), nullable=True),
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
        sa.CheckConstraint(
            "(possui_responsavel AND responsavel_nome IS NOT NULL"
            " AND responsavel_cpf IS NOT NULL AND responsavel_telefone IS NOT NULL"
            " AND cpf IS NULL AND telefone IS NULL)"
            " OR (NOT possui_responsavel AND cpf IS NOT NULL AND telefone IS NOT NULL"
            " AND responsavel_nome IS NULL AND responsavel_cpf IS NULL"
            " AND responsavel_telefone IS NULL)",
            name="ck_aluno_dados_do_responsavel",
        ),
    )


def downgrade() -> None:
    op.drop_table("aluno")

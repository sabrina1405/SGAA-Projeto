"""professor

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "professor",
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("cnpj", sa.String(14), nullable=True, unique=True),
        sa.Column("chave_pix", sa.String(77), nullable=True, unique=True),
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
    # Contas de professor criadas antes desta tabela existir.
    op.execute(
        "INSERT INTO professor (usuario_id)"
        " SELECT id FROM usuario WHERE tipo = 'professor'"
    )


def downgrade() -> None:
    op.drop_table("professor")

"""grupo e grupo_aluno

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grupo",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("titulo", sa.String(50), nullable=False),
        sa.Column("descricao", sa.String(100), nullable=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
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
    op.create_index("ix_grupo_professor_id", "grupo", ["professor_id"])

    op.create_table(
        "grupo_aluno",
        sa.Column(
            "grupo_id",
            sa.Integer(),
            sa.ForeignKey("grupo.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_grupo_aluno_aluno_id", "grupo_aluno", ["aluno_id"])


def downgrade() -> None:
    op.drop_index("ix_grupo_aluno_aluno_id", table_name="grupo_aluno")
    op.drop_table("grupo_aluno")
    op.drop_index("ix_grupo_professor_id", table_name="grupo")
    op.drop_table("grupo")

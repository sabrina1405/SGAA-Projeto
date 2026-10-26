"""recado_geral, recado, recado_aluno e recado_grupo

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-25

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recado_geral",
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("conteudo", sa.Text(), nullable=False),
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
        "recado",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("todos_alunos", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("todos_grupos", sa.Boolean(), server_default="false", nullable=False),
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
            "data_fim IS NULL OR data_fim >= data_inicio", name="ck_recado_periodo"
        ),
    )
    op.create_index("ix_recado_professor_id", "recado", ["professor_id"])
    op.create_table(
        "recado_aluno",
        sa.Column(
            "recado_id",
            sa.Integer(),
            sa.ForeignKey("recado.id", ondelete="CASCADE"),
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
    op.create_index("ix_recado_aluno_aluno_id", "recado_aluno", ["aluno_id"])
    op.create_table(
        "recado_grupo",
        sa.Column(
            "recado_id",
            sa.Integer(),
            sa.ForeignKey("recado.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "grupo_id",
            sa.Integer(),
            sa.ForeignKey("grupo.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_recado_grupo_grupo_id", "recado_grupo", ["grupo_id"])


def downgrade() -> None:
    op.drop_index("ix_recado_grupo_grupo_id", table_name="recado_grupo")
    op.drop_table("recado_grupo")
    op.drop_index("ix_recado_aluno_aluno_id", table_name="recado_aluno")
    op.drop_table("recado_aluno")
    op.drop_index("ix_recado_professor_id", table_name="recado")
    op.drop_table("recado")
    op.drop_table("recado_geral")

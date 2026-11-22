"""pasta, pasta_aluno, pasta_grupo e anexo_pasta

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pasta",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "pasta_pai_id", sa.Integer(), sa.ForeignKey("pasta.id"), nullable=True
        ),
        sa.Column("raiz_id", sa.Integer(), sa.ForeignKey("pasta.id"), nullable=True),
        sa.Column("nome", sa.String(80), nullable=False),
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
    )
    op.create_index("ix_pasta_professor_id", "pasta", ["professor_id"])
    op.create_index("ix_pasta_pasta_pai_id", "pasta", ["pasta_pai_id"])
    op.create_index("ix_pasta_raiz_id", "pasta", ["raiz_id"])
    op.create_index(
        "uq_pasta_nome_no_lugar",
        "pasta",
        [
            sa.text("professor_id"),
            sa.text("coalesce(pasta_pai_id, 0)"),
            sa.text("lower(nome)"),
        ],
        unique=True,
        postgresql_where=sa.text("deletado_em IS NULL"),
    )
    op.create_table(
        "pasta_aluno",
        sa.Column(
            "pasta_id",
            sa.Integer(),
            sa.ForeignKey("pasta.id", ondelete="CASCADE"),
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
    op.create_index("ix_pasta_aluno_aluno_id", "pasta_aluno", ["aluno_id"])
    op.create_table(
        "pasta_grupo",
        sa.Column(
            "pasta_id",
            sa.Integer(),
            sa.ForeignKey("pasta.id", ondelete="CASCADE"),
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
    op.create_index("ix_pasta_grupo_grupo_id", "pasta_grupo", ["grupo_id"])
    op.create_table(
        "anexo_pasta",
        sa.Column(
            "pasta_id",
            sa.Integer(),
            sa.ForeignKey("pasta.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "arquivo_id",
            sa.Integer(),
            sa.ForeignKey("arquivo.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_anexo_pasta_pasta_id", "anexo_pasta", ["pasta_id"])


def downgrade() -> None:
    op.drop_index("ix_anexo_pasta_pasta_id", table_name="anexo_pasta")
    op.drop_table("anexo_pasta")
    op.drop_index("ix_pasta_grupo_grupo_id", table_name="pasta_grupo")
    op.drop_table("pasta_grupo")
    op.drop_index("ix_pasta_aluno_aluno_id", table_name="pasta_aluno")
    op.drop_table("pasta_aluno")
    op.drop_index("uq_pasta_nome_no_lugar", table_name="pasta")
    op.drop_index("ix_pasta_raiz_id", table_name="pasta")
    op.drop_index("ix_pasta_pasta_pai_id", table_name="pasta")
    op.drop_index("ix_pasta_professor_id", table_name="pasta")
    op.drop_table("pasta")

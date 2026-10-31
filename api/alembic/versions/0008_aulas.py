"""aula, aula_aluno e aula_grupo

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _auditoria() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "aula",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
        sa.Column("serie_id", sa.Integer(), sa.ForeignKey("aula.id"), nullable=True),
        sa.Column(
            "reposicao_de_aula_id",
            sa.Integer(),
            sa.ForeignKey("aula.id"),
            nullable=True,
        ),
        sa.Column("titulo", sa.String(75), nullable=False),
        sa.Column("descricao", sa.String(150), nullable=True),
        sa.Column("anotacoes", sa.Text(), nullable=True),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("agendada", "realizada", "cancelada", name="status_aula_enum"),
            server_default="agendada",
            nullable=False,
        ),
        sa.Column("motivo_cancelamento", sa.String(150), nullable=True),
        *_auditoria(),
        sa.Column("deletado_em", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("fim > inicio", name="ck_aula_horario"),
    )
    op.create_index("ix_aula_professor_id_inicio", "aula", ["professor_id", "inicio"])
    op.create_index("ix_aula_serie_id", "aula", ["serie_id"])
    op.create_table(
        "aula_aluno",
        sa.Column("id", sa.Integer(), sa.Identity(), unique=True, nullable=False),
        sa.Column(
            "aula_id",
            sa.Integer(),
            sa.ForeignKey("aula.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "status",
            sa.Enum("ativa", "cancelada", name="status_participacao_enum"),
            server_default="ativa",
            nullable=False,
        ),
        sa.Column("motivo_cancelamento", sa.String(150), nullable=True),
        sa.Column("cancelada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("repor", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "reposta_em_aula_id",
            sa.Integer(),
            sa.ForeignKey("aula.id"),
            nullable=True,
        ),
        *_auditoria(),
    )
    op.create_index("ix_aula_aluno_aluno_id", "aula_aluno", ["aluno_id"])
    op.create_table(
        "aula_grupo",
        sa.Column(
            "aula_id",
            sa.Integer(),
            sa.ForeignKey("aula.id", ondelete="CASCADE"),
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
    op.create_index("ix_aula_grupo_grupo_id", "aula_grupo", ["grupo_id"])


def downgrade() -> None:
    op.drop_index("ix_aula_grupo_grupo_id", table_name="aula_grupo")
    op.drop_table("aula_grupo")
    op.drop_index("ix_aula_aluno_aluno_id", table_name="aula_aluno")
    op.drop_table("aula_aluno")
    op.drop_index("ix_aula_serie_id", table_name="aula")
    op.drop_index("ix_aula_professor_id_inicio", table_name="aula")
    op.drop_table("aula")
    sa.Enum(name="status_participacao_enum").drop(op.get_bind())
    sa.Enum(name="status_aula_enum").drop(op.get_bind())

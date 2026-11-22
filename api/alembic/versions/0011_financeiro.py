"""plano_cobranca e cobranca

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

frequencia_plano_enum = postgresql.ENUM(
    "mensal", "semanal", name="frequencia_plano_enum", create_type=False
)
status_cobranca_enum = postgresql.ENUM(
    "pendente", "paga", "cancelada", name="status_cobranca_enum", create_type=False
)


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
        sa.Column("deletado_em", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    frequencia_plano_enum.create(op.get_bind())
    status_cobranca_enum.create(op.get_bind())
    op.create_table(
        "plano_cobranca",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("descricao", sa.String(100), nullable=False),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
        sa.Column("frequencia", frequencia_plano_enum, nullable=False),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("inicio", sa.Date(), nullable=False),
        sa.Column("fim", sa.Date(), nullable=True),
        *_auditoria(),
        sa.CheckConstraint("valor_centavos > 0", name="ck_plano_cobranca_valor"),
        sa.CheckConstraint(
            "(frequencia = 'mensal' AND dia_vencimento BETWEEN 1 AND 31)"
            " OR (frequencia = 'semanal' AND dia_vencimento BETWEEN 0 AND 6)",
            name="ck_plano_cobranca_dia",
        ),
        sa.CheckConstraint(
            "fim IS NULL OR fim >= inicio", name="ck_plano_cobranca_periodo"
        ),
    )
    op.create_index(
        "ix_plano_cobranca_professor_id", "plano_cobranca", ["professor_id"]
    )
    op.create_index("ix_plano_cobranca_aluno_id", "plano_cobranca", ["aluno_id"])
    op.create_table(
        "cobranca",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plano_id",
            sa.Integer(),
            sa.ForeignKey("plano_cobranca.id"),
            nullable=True,
        ),
        sa.Column("descricao", sa.String(100), nullable=False),
        sa.Column("valor_centavos", sa.Integer(), nullable=False),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column(
            "status",
            status_cobranca_enum,
            server_default="pendente",
            nullable=False,
        ),
        sa.Column("paga_em", sa.DateTime(timezone=True), nullable=True),
        *_auditoria(),
        sa.CheckConstraint("valor_centavos > 0", name="ck_cobranca_valor"),
        sa.UniqueConstraint(
            "plano_id", "vencimento", name="uq_cobranca_plano_vencimento"
        ),
    )
    op.create_index(
        "ix_cobranca_professor_vencimento", "cobranca", ["professor_id", "vencimento"]
    )
    op.create_index(
        "ix_cobranca_aluno_vencimento", "cobranca", ["aluno_id", "vencimento"]
    )


def downgrade() -> None:
    op.drop_index("ix_cobranca_aluno_vencimento", table_name="cobranca")
    op.drop_index("ix_cobranca_professor_vencimento", table_name="cobranca")
    op.drop_table("cobranca")
    op.drop_index("ix_plano_cobranca_aluno_id", table_name="plano_cobranca")
    op.drop_index("ix_plano_cobranca_professor_id", table_name="plano_cobranca")
    op.drop_table("plano_cobranca")
    status_cobranca_enum.drop(op.get_bind())
    frequencia_plano_enum.drop(op.get_bind())

"""arquivo, atividade, destinatários, anexos e entrega_atividade

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-31

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
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
        sa.Column("deletado_em", sa.DateTime(timezone=True), nullable=True),
    ]


def _criado_em() -> sa.Column:
    return sa.Column(
        "criado_em",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "arquivo",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "enviado_por_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("tipo_mime", sa.String(100), nullable=False),
        sa.Column("tamanho", sa.Integer(), nullable=False),
        sa.Column("drive_file_id", sa.String(100), unique=True, nullable=True),
        sa.Column("drive_url", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pendente", "confirmado", "remover", name="status_arquivo_enum"),
            server_default="pendente",
            nullable=False,
        ),
        *_auditoria(),
    )
    op.create_index("ix_arquivo_enviado_por_id", "arquivo", ["enviado_por_id"])
    op.create_index(
        "ix_arquivo_limpeza",
        "arquivo",
        ["criado_em"],
        postgresql_where=sa.text("deletado_em IS NULL"),
    )
    op.create_table(
        "atividade",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "professor_id",
            sa.Integer(),
            sa.ForeignKey("professor.usuario_id"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(75), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column(
            "permite_envio_arquivo",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("liberar_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vence_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("todos_alunos", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("todos_grupos", sa.Boolean(), server_default="false", nullable=False),
        *_auditoria(),
        sa.CheckConstraint("vence_em > liberar_em", name="ck_atividade_periodo"),
    )
    op.create_index(
        "ix_atividade_professor_id_vence_em",
        "atividade",
        ["professor_id", "vence_em"],
    )
    op.create_table(
        "atividade_aluno",
        sa.Column(
            "atividade_id",
            sa.Integer(),
            sa.ForeignKey("atividade.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _criado_em(),
    )
    op.create_index("ix_atividade_aluno_aluno_id", "atividade_aluno", ["aluno_id"])
    op.create_table(
        "atividade_grupo",
        sa.Column(
            "atividade_id",
            sa.Integer(),
            sa.ForeignKey("atividade.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "grupo_id",
            sa.Integer(),
            sa.ForeignKey("grupo.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        _criado_em(),
    )
    op.create_index("ix_atividade_grupo_grupo_id", "atividade_grupo", ["grupo_id"])
    op.create_table(
        "anexo_atividade",
        sa.Column(
            "atividade_id",
            sa.Integer(),
            sa.ForeignKey("atividade.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "arquivo_id",
            sa.Integer(),
            sa.ForeignKey("arquivo.id", ondelete="CASCADE"),
            primary_key=True,
            unique=True,
        ),
    )
    op.create_table(
        "entrega_atividade",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "atividade_id",
            sa.Integer(),
            sa.ForeignKey("atividade.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey("aluno.usuario_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resposta", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("enviado", "entregue_com_atraso", name="status_entrega_enum"),
            server_default="enviado",
            nullable=False,
        ),
        sa.Column("enviada_em", sa.DateTime(timezone=True), nullable=False),
        *_auditoria(),
        sa.UniqueConstraint(
            "atividade_id", "aluno_id", name="uq_entrega_atividade_atividade_aluno"
        ),
    )
    op.create_index("ix_entrega_atividade_aluno_id", "entrega_atividade", ["aluno_id"])
    op.create_table(
        "anexo_entrega",
        sa.Column(
            "entrega_id",
            sa.Integer(),
            sa.ForeignKey("entrega_atividade.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "arquivo_id",
            sa.Integer(),
            sa.ForeignKey("arquivo.id", ondelete="CASCADE"),
            primary_key=True,
            unique=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("anexo_entrega")
    op.drop_index("ix_entrega_atividade_aluno_id", table_name="entrega_atividade")
    op.drop_table("entrega_atividade")
    op.drop_table("anexo_atividade")
    op.drop_index("ix_atividade_grupo_grupo_id", table_name="atividade_grupo")
    op.drop_table("atividade_grupo")
    op.drop_index("ix_atividade_aluno_aluno_id", table_name="atividade_aluno")
    op.drop_table("atividade_aluno")
    op.drop_index("ix_atividade_professor_id_vence_em", table_name="atividade")
    op.drop_table("atividade")
    op.drop_index("ix_arquivo_limpeza", table_name="arquivo")
    op.drop_index("ix_arquivo_enviado_por_id", table_name="arquivo")
    op.drop_table("arquivo")
    sa.Enum(name="status_entrega_enum").drop(op.get_bind())
    sa.Enum(name="status_arquivo_enum").drop(op.get_bind())

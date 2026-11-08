"""envio_email

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "envio_email",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "notificacao_id",
            sa.Integer(),
            sa.ForeignKey("notificacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "notificacao_id", "usuario_id", name="uq_envio_email_notificacao_usuario"
        ),
    )
    op.create_index("ix_envio_email_usuario_id", "envio_email", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_envio_email_usuario_id", table_name="envio_email")
    op.drop_table("envio_email")

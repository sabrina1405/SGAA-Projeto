from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class Aluno(AuditoriaMixin, Base):
    """Perfil do aluno, criado quando ele conclui o primeiro acesso."""

    __tablename__ = "aluno"
    __table_args__ = (
        # Menor de idade: só os dados do responsável. Maior: só os do aluno.
        CheckConstraint(
            "(possui_responsavel AND responsavel_nome IS NOT NULL"
            " AND responsavel_cpf IS NOT NULL AND responsavel_telefone IS NOT NULL"
            " AND cpf IS NULL AND telefone IS NULL)"
            " OR (NOT possui_responsavel AND cpf IS NOT NULL AND telefone IS NOT NULL"
            " AND responsavel_nome IS NULL AND responsavel_cpf IS NULL"
            " AND responsavel_telefone IS NULL)",
            name="ck_aluno_dados_do_responsavel",
        ),
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    data_nascimento: Mapped[date] = mapped_column(Date)
    possui_responsavel: Mapped[bool] = mapped_column(Boolean)
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(11))
    # Sem unicidade: irmãos podem ter o mesmo responsável.
    responsavel_nome: Mapped[str | None] = mapped_column(String(100))
    responsavel_cpf: Mapped[str | None] = mapped_column(String(11))
    responsavel_telefone: Mapped[str | None] = mapped_column(String(11))

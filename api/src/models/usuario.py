import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class TipoUsuario(enum.StrEnum):
    PROFESSOR = "professor"
    ALUNO = "aluno"


class Usuario(AuditoriaMixin, Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(80), unique=True)
    # Hash Argon2id. Nulo até o usuário definir a senha no primeiro acesso.
    senha: Mapped[str | None] = mapped_column(String(150))
    tipo: Mapped[TipoUsuario] = mapped_column(
        Enum(
            TipoUsuario,
            name="tipo_usuario_enum",
            values_callable=lambda tipos: [tipo.value for tipo in tipos],
        )
    )
    versao_token: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    tentativas_login: Mapped[int] = mapped_column(
        Integer, server_default="0", default=0
    )
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

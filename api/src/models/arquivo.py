import enum

from sqlalchemy import Enum, ForeignKey, Identity, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditoriaMixin, Base


class StatusArquivo(enum.StrEnum):
    PENDENTE = "pendente"  # sessão aberta, upload ainda não confirmado
    CONFIRMADO = "confirmado"
    REMOVER = "remover"  # a tarefa agendada apaga do Drive


class Arquivo(AuditoriaMixin, Base):
    """Arquivo guardado no Google Drive. Sobe antes de salvar o formulário: sem
    vínculo com uma atividade ou entrega, a tarefa agendada o apaga."""

    __tablename__ = "arquivo"
    __table_args__ = (
        Index(
            "ix_arquivo_limpeza",
            "criado_em",
            postgresql_where=text("deletado_em IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    enviado_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(150))
    tipo_mime: Mapped[str] = mapped_column(String(100))
    tamanho: Mapped[int] = mapped_column(Integer)
    drive_file_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    drive_url: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[StatusArquivo] = mapped_column(
        Enum(
            StatusArquivo,
            name="status_arquivo_enum",
            values_callable=lambda itens: [item.value for item in itens],
        ),
        server_default=StatusArquivo.PENDENTE.value,
        default=StatusArquivo.PENDENTE,
    )

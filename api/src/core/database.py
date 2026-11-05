from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime, Engine, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import NullPool

from src.core.config import obter_config


class Base(DeclarativeBase):
    pass


class AuditoriaMixin:
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deletado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


@lru_cache
def obter_engine() -> Engine:
    # Em serverless cada instância abre as próprias conexões: sem pool local, e
    # sem prepared statements para funcionar atrás de um pooler em modo transação.
    return create_engine(
        obter_config().database_url,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )


def obter_sessao() -> Iterator[Session]:
    with Session(obter_engine(), expire_on_commit=False) as sessao:
        yield sessao

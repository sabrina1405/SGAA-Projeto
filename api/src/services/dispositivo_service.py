from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.core.security import agora
from src.models.notificacao import Dispositivo
from src.models.usuario import Usuario


def registrar_dispositivo(
    sessao: Session, usuario: Usuario, token: str, plataforma: str | None
) -> None:
    """Um token já conhecido passa para o usuário atual (troca de conta no aparelho)."""
    dispositivo = sessao.scalar(select(Dispositivo).where(Dispositivo.token == token))
    if dispositivo is None:
        dispositivo = Dispositivo(token=token)
        sessao.add(dispositivo)
    dispositivo.usuario_id = usuario.id
    dispositivo.plataforma = plataforma
    dispositivo.deletado_em = None
    sessao.commit()


def remover_dispositivo(sessao: Session, usuario: Usuario, token: str) -> None:
    """Token de outro usuário ou desconhecido não é erro: o logout segue igual."""
    sessao.execute(
        update(Dispositivo)
        .where(
            Dispositivo.token == token,
            Dispositivo.usuario_id == usuario.id,
            Dispositivo.deletado_em.is_(None),
        )
        .values(deletado_em=agora())
    )
    sessao.commit()


def remover_todos(sessao: Session, usuario: Usuario) -> None:
    """Não faz commit: acompanha a invalidação dos tokens de acesso."""
    sessao.execute(
        update(Dispositivo)
        .where(Dispositivo.usuario_id == usuario.id, Dispositivo.deletado_em.is_(None))
        .values(deletado_em=agora())
    )

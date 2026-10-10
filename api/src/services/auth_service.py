import hmac
import logging
from datetime import timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.core.config import obter_config
from src.core.email import EnviadorEmail
from src.core.security import (
    agora,
    gerar_codigo,
    hash_codigo,
    hash_ficticio,
    hash_senha,
    precisa_rehash,
    verificar_senha,
)
from src.models.codigo_verificacao import CodigoVerificacao
from src.models.usuario import Usuario

logger = logging.getLogger(__name__)

MAX_TENTATIVAS_LOGIN = 5
DURACAO_BLOQUEIO_LOGIN = timedelta(minutes=15)

MAX_TENTATIVAS_CODIGO = 5
INTERVALO_MINIMO_ENTRE_CODIGOS = timedelta(seconds=60)
JANELA_LIMITE_CODIGOS = timedelta(hours=1)
MAX_CODIGOS_POR_JANELA = 5


class CredenciaisInvalidas(Exception):
    pass


class CodigoInvalido(Exception):
    pass


class LimiteCodigosExcedido(Exception):
    pass


def buscar_usuario_ativo(
    sessao: Session, email: str, *, travar: bool = False
) -> Usuario | None:
    consulta = select(Usuario).where(
        Usuario.email == email, Usuario.deletado_em.is_(None)
    )
    if travar:
        consulta = consulta.with_for_update()
    return sessao.scalar(consulta)


def autenticar(sessao: Session, email: str, senha: str) -> Usuario:
    usuario = buscar_usuario_ativo(sessao, email, travar=True)
    momento = agora()

    bloqueado = (
        usuario is not None
        and usuario.bloqueado_ate is not None
        and usuario.bloqueado_ate > momento
    )
    if usuario is None or usuario.senha is None or bloqueado:
        # Gasta o mesmo tempo de uma verificação real para não revelar pelo
        # tempo de resposta se o e-mail existe.
        verificar_senha(senha, hash_ficticio())
        sessao.rollback()
        raise CredenciaisInvalidas

    if not verificar_senha(senha, usuario.senha):
        usuario.tentativas_login += 1
        if usuario.tentativas_login >= MAX_TENTATIVAS_LOGIN:
            usuario.tentativas_login = 0
            usuario.bloqueado_ate = momento + DURACAO_BLOQUEIO_LOGIN
        sessao.commit()
        raise CredenciaisInvalidas

    usuario.tentativas_login = 0
    usuario.bloqueado_ate = None
    if precisa_rehash(usuario.senha):
        usuario.senha = hash_senha(senha)
    sessao.commit()
    return usuario


def emitir_codigo(sessao: Session, usuario: Usuario, validade: timedelta) -> str:
    """Gera um código novo para o usuário, invalidando os anteriores.

    Não faz commit. Levanta LimiteCodigosExcedido se o usuário pediu códigos
    demais em pouco tempo.
    """
    momento = agora()
    # Serializa emissões concorrentes do mesmo usuário.
    sessao.execute(select(Usuario.id).where(Usuario.id == usuario.id).with_for_update())

    inicio_janela = momento - JANELA_LIMITE_CODIGOS
    quantidade, mais_recente = sessao.execute(
        select(func.count(), func.max(CodigoVerificacao.criado_em)).where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.criado_em > inicio_janela,
        )
    ).one()
    if quantidade >= MAX_CODIGOS_POR_JANELA or (
        mais_recente is not None
        and momento - mais_recente < INTERVALO_MINIMO_ENTRE_CODIGOS
    ):
        raise LimiteCodigosExcedido

    # Os códigos da última hora ficam (já inutilizados) para a contagem do limite.
    sessao.execute(
        delete(CodigoVerificacao).where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.criado_em <= inicio_janela,
        )
    )
    sessao.execute(
        update(CodigoVerificacao)
        .where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.usado_em.is_(None),
        )
        .values(usado_em=momento)
    )

    codigo = gerar_codigo()
    sessao.add(
        CodigoVerificacao(
            usuario_id=usuario.id,
            codigo_hash=hash_codigo(usuario.id, codigo),
            expira_em=momento + validade,
            criado_em=momento,
        )
    )
    sessao.flush()
    return codigo


def solicitar_codigo(
    sessao: Session,
    enviador: EnviadorEmail,
    email: str,
    *,
    primeiro_acesso: bool = False,
) -> None:
    """Envia um código por e-mail, se o e-mail for de um usuário ativo.

    Conta sem senha ainda não concluiu o primeiro acesso: o código de primeiro
    acesso só sai para ela, e o de redefinição só para quem já tem senha.
    Nunca informa ao chamador se o e-mail existe.
    """
    usuario = buscar_usuario_ativo(sessao, email)
    if usuario is None or (usuario.senha is None) != primeiro_acesso:
        return

    minutos = obter_config().codigo_expira_minutos
    try:
        codigo = emitir_codigo(sessao, usuario, timedelta(minutes=minutos))
    except LimiteCodigosExcedido:
        sessao.rollback()
        return
    sessao.commit()

    finalidade = (
        "concluir seu primeiro acesso" if primeiro_acesso else "redefinir sua senha"
    )
    try:
        enviador.enviar(
            usuario.email,
            f"SGAA - código para {finalidade}",
            f"Olá, {usuario.nome_completo}.\n\n"
            f"Seu código para {finalidade} é: {codigo}\n\n"
            f"Ele vale por {minutos} minutos. "
            "Se você não fez esse pedido, ignore este e-mail.",
        )
    except Exception:
        logger.exception("Falha ao enviar código (usuario_id=%s)", usuario.id)


def _consumir_codigo(sessao: Session, usuario: Usuario, codigo: str) -> None:
    """Marca o código ativo do usuário como usado, sem fazer commit.

    Levanta CodigoInvalido; uma tentativa errada é contada e gravada.
    """
    registro = sessao.scalar(
        select(CodigoVerificacao)
        .where(
            CodigoVerificacao.usuario_id == usuario.id,
            CodigoVerificacao.usado_em.is_(None),
        )
        .order_by(CodigoVerificacao.criado_em.desc(), CodigoVerificacao.id.desc())
        .limit(1)
        .with_for_update()
    )
    momento = agora()
    if (
        registro is None
        or registro.expira_em <= momento
        or registro.tentativas >= MAX_TENTATIVAS_CODIGO
    ):
        sessao.rollback()
        raise CodigoInvalido

    if not hmac.compare_digest(registro.codigo_hash, hash_codigo(usuario.id, codigo)):
        registro.tentativas += 1
        sessao.commit()
        raise CodigoInvalido

    registro.usado_em = momento


def redefinir_senha(sessao: Session, email: str, codigo: str, nova_senha: str) -> None:
    usuario = buscar_usuario_ativo(sessao, email)
    # Sem senha, o caminho é o primeiro acesso, que também exige os dados do perfil.
    if usuario is None or usuario.senha is None:
        raise CodigoInvalido

    _consumir_codigo(sessao, usuario, codigo)
    definir_senha(usuario, nova_senha)
    sessao.commit()


def validar_codigo_primeiro_acesso(sessao: Session, email: str, codigo: str) -> Usuario:
    """Consome o código e devolve o usuário que pode concluir o primeiro acesso."""
    usuario = buscar_usuario_ativo(sessao, email)
    if usuario is None or usuario.senha is not None:
        raise CodigoInvalido

    _consumir_codigo(sessao, usuario, codigo)
    sessao.commit()
    return usuario


def definir_senha(usuario: Usuario, nova_senha: str) -> None:
    """Grava a senha e derruba os tokens já emitidos. Não faz commit."""
    usuario.senha = hash_senha(nova_senha)
    usuario.tentativas_login = 0
    usuario.bloqueado_ate = None
    invalidar_tokens(usuario)


def invalidar_tokens(usuario: Usuario) -> None:
    """Invalida todos os tokens já emitidos para o usuário. Não faz commit."""
    usuario.versao_token += 1

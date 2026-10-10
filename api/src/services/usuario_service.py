import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.config import obter_config
from src.core.email import EnviadorEmail
from src.models.aluno import Aluno
from src.models.usuario import TipoUsuario, Usuario
from src.services.auth_service import definir_senha, emitir_codigo

logger = logging.getLogger(__name__)


class EmailJaCadastrado(Exception):
    pass


class CpfJaCadastrado(Exception):
    pass


class PrimeiroAcessoJaConcluido(Exception):
    pass


class FalhaEnvioEmail(Exception):
    pass


def criar_usuario(
    sessao: Session,
    *,
    nome_completo: str,
    email: str,
    tipo: TipoUsuario,
    senha_hash: str | None = None,
) -> Usuario:
    """Insere o usuário sem fazer commit. Levanta EmailJaCadastrado."""
    # Inclui usuários com soft delete: o e-mail deles continua reservado.
    if sessao.scalar(select(Usuario.id).where(Usuario.email == email)) is not None:
        raise EmailJaCadastrado

    usuario = Usuario(
        nome_completo=nome_completo, email=email, tipo=tipo, senha=senha_hash
    )
    sessao.add(usuario)
    try:
        sessao.flush()
    except IntegrityError as erro:
        sessao.rollback()
        raise EmailJaCadastrado from erro
    return usuario


def criar_aluno(
    sessao: Session, enviador: EnviadorEmail, *, nome_completo: str, email: str
) -> Usuario:
    """Cria o aluno sem senha e envia o código de primeiro acesso."""
    usuario = criar_usuario(
        sessao, nome_completo=nome_completo, email=email, tipo=TipoUsuario.ALUNO
    )
    horas = obter_config().convite_expira_horas
    codigo = emitir_codigo(sessao, usuario, timedelta(hours=horas))

    try:
        enviador.enviar(
            usuario.email,
            "SGAA - seu acesso foi criado",
            f"Olá, {usuario.nome_completo}.\n\n"
            "Sua conta no SGAA foi criada. Para ativá-la, abra o app, "
            f'escolha "Primeiro acesso" e informe o código: {codigo}\n\n'
            f"Ele vale por {horas} horas. Depois disso, peça um novo código no app.",
        )
    except Exception as erro:
        # Sem o e-mail o aluno não consegue entrar: desfaz para o cadastro ser refeito.
        sessao.rollback()
        logger.exception("Falha ao enviar código de primeiro acesso")
        raise FalhaEnvioEmail from erro

    sessao.commit()
    return usuario


def concluir_primeiro_acesso_aluno(
    sessao: Session,
    usuario: Usuario,
    *,
    data_nascimento: date,
    possui_responsavel: bool,
    cpf: str,
    telefone: str,
    responsavel_nome: str | None,
    nova_senha: str,
) -> None:
    """Grava o perfil do aluno e a senha na mesma transação.

    `cpf` e `telefone` são do responsável quando `possui_responsavel`.
    Levanta PrimeiroAcessoJaConcluido e CpfJaCadastrado.
    """
    # Serializa envios concorrentes do mesmo formulário.
    sessao.refresh(usuario, with_for_update=True)
    if usuario.senha is not None:
        sessao.rollback()
        raise PrimeiroAcessoJaConcluido

    if possui_responsavel:
        aluno = Aluno(
            usuario_id=usuario.id,
            data_nascimento=data_nascimento,
            possui_responsavel=True,
            responsavel_nome=responsavel_nome,
            responsavel_cpf=cpf,
            responsavel_telefone=telefone,
        )
    else:
        cpf_em_uso = sessao.scalar(select(Aluno.usuario_id).where(Aluno.cpf == cpf))
        if cpf_em_uso is not None:
            sessao.rollback()
            raise CpfJaCadastrado
        aluno = Aluno(
            usuario_id=usuario.id,
            data_nascimento=data_nascimento,
            possui_responsavel=False,
            cpf=cpf,
            telefone=telefone,
        )
    sessao.add(aluno)
    definir_senha(usuario, nova_senha)
    try:
        sessao.commit()
    except IntegrityError as erro:
        sessao.rollback()
        raise CpfJaCadastrado from erro

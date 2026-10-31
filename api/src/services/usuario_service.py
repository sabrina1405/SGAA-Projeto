import logging
import unicodedata
from collections.abc import Sequence
from datetime import date, timedelta

from sqlalchemy import Row, Select, String, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.config import obter_config
from src.core.email import EnviadorEmail
from src.models.aluno import Aluno
from src.models.professor import Professor
from src.models.usuario import TipoUsuario, Usuario
from src.services.auth_service import definir_senha, emitir_codigo

logger = logging.getLogger(__name__)


class EmailJaCadastrado(Exception):
    pass


class CpfJaCadastrado(Exception):
    pass


class CnpjJaCadastrado(Exception):
    pass


class ChavePixJaCadastrada(Exception):
    pass


class PrimeiroAcessoJaConcluido(Exception):
    pass


class FalhaEnvioEmail(Exception):
    pass


class AlunoNaoEncontrado(Exception):
    pass


class PerfilNaoEncontrado(Exception):
    pass


class CamposNaoPermitidos(Exception):
    def __init__(self, campos: list[str]) -> None:
        super().__init__(campos)
        self.campos = campos


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


def criar_professor(
    sessao: Session,
    *,
    nome_completo: str,
    email: str,
    senha_hash: str,
    cnpj: str | None = None,
    chave_pix: str | None = None,
) -> Usuario:
    """Insere o usuário e os dados de professor, sem fazer commit.

    Levanta EmailJaCadastrado, CnpjJaCadastrado e ChavePixJaCadastrada.
    """
    if cnpj is not None and sessao.scalar(
        select(Professor.usuario_id).where(Professor.cnpj == cnpj)
    ):
        raise CnpjJaCadastrado
    if chave_pix is not None and sessao.scalar(
        select(Professor.usuario_id).where(Professor.chave_pix == chave_pix)
    ):
        raise ChavePixJaCadastrada

    usuario = criar_usuario(
        sessao,
        nome_completo=nome_completo,
        email=email,
        tipo=TipoUsuario.PROFESSOR,
        senha_hash=senha_hash,
    )
    sessao.add(Professor(usuario_id=usuario.id, cnpj=cnpj, chave_pix=chave_pix))
    sessao.flush()
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


def _sem_acentos(texto: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


# Ordem alfabética sem considerar maiúsculas nem acentos, estável entre páginas.
ORDEM_DOS_ALUNOS = (func.lower(func.unaccent(Usuario.nome_completo)), Usuario.id)


def consulta_alunos() -> Select:
    """Alunos ativos que concluíram o primeiro acesso, com o telefone de contato."""
    return (
        select(
            Usuario.id,
            Usuario.nome_completo,
            Usuario.email,
            func.coalesce(Aluno.telefone, Aluno.responsavel_telefone).label("telefone"),
        )
        .join(Aluno, Aluno.usuario_id == Usuario.id)
        .where(
            Usuario.tipo == TipoUsuario.ALUNO,
            Usuario.deletado_em.is_(None),
            Usuario.senha.is_not(None),
        )
    )


def listar_alunos(
    sessao: Session, *, pagina: int, tamanho: int, busca: str | None = None
) -> tuple[Sequence[Row], int]:
    """Página de alunos que concluíram o primeiro acesso, e o total sem paginar.

    `busca` casa com trecho do nome ou do e-mail, sem diferenciar maiúsculas
    nem acentos.
    """
    consulta = consulta_alunos()
    if busca:
        # O termo vai como literal, sem acentos, para o autoescape tratar % e _.
        termo = _sem_acentos(busca)
        consulta = consulta.where(
            or_(
                func.unaccent(Usuario.nome_completo, type_=String).icontains(
                    termo, autoescape=True
                ),
                func.unaccent(Usuario.email, type_=String).icontains(
                    termo, autoescape=True
                ),
            )
        )

    total = sessao.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = sessao.execute(
        consulta.order_by(*ORDEM_DOS_ALUNOS)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_aluno(sessao: Session, aluno_id: int) -> tuple[Usuario, Aluno | None]:
    """Devolve o aluno e o perfil, que é None antes do primeiro acesso.

    Levanta AlunoNaoEncontrado.
    """
    usuario = sessao.get(Usuario, aluno_id)
    if (
        usuario is None
        or usuario.deletado_em is not None
        or usuario.tipo != TipoUsuario.ALUNO
    ):
        raise AlunoNaoEncontrado
    return usuario, sessao.get(Aluno, usuario.id)


def obter_perfil_aluno(sessao: Session, usuario: Usuario) -> Aluno:
    """Levanta PerfilNaoEncontrado."""
    aluno = sessao.get(Aluno, usuario.id)
    if aluno is None:
        raise PerfilNaoEncontrado
    return aluno


def atualizar_perfil_aluno(
    sessao: Session,
    usuario: Usuario,
    *,
    nome_completo: str | None = None,
    telefone: str | None = None,
    responsavel_nome: str | None = None,
    responsavel_cpf: str | None = None,
    responsavel_telefone: str | None = None,
) -> Aluno:
    """Altera só os campos informados (None significa "não alterar").

    Quem tem responsável só altera os dados dele; quem não tem, só o próprio
    telefone. Levanta PerfilNaoEncontrado e CamposNaoPermitidos.
    """
    aluno = obter_perfil_aluno(sessao, usuario)

    do_aluno = {"telefone": telefone}
    do_responsavel = {
        "responsavel_nome": responsavel_nome,
        "responsavel_cpf": responsavel_cpf,
        "responsavel_telefone": responsavel_telefone,
    }
    # Vale o que foi gravado no primeiro acesso, não a idade de hoje.
    permitidos, proibidos = (
        (do_responsavel, do_aluno)
        if aluno.possui_responsavel
        else (do_aluno, do_responsavel)
    )
    nao_permitidos = [campo for campo, valor in proibidos.items() if valor is not None]
    if nao_permitidos:
        raise CamposNaoPermitidos(nao_permitidos)

    if nome_completo is not None:
        usuario.nome_completo = nome_completo
    for campo, valor in permitidos.items():
        if valor is not None:
            setattr(aluno, campo, valor)
    sessao.commit()
    return aluno

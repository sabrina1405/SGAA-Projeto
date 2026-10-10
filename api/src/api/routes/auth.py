from fastapi import APIRouter, HTTPException, status

from src.api.deps import (
    EnviadorEmailDep,
    SessaoDep,
    UsuarioAtual,
    UsuarioPrimeiroAcesso,
)
from src.core.security import (
    VALIDADE_TOKEN_PRIMEIRO_ACESSO,
    criar_token,
    criar_token_primeiro_acesso,
    segundos_validade_token,
)
from src.models.usuario import TipoUsuario, Usuario
from src.schemas.aluno import PrimeiroAcessoAlunoEntrada
from src.schemas.auth import (
    EsqueciSenhaEntrada,
    LoginEntrada,
    MensagemResposta,
    PrimeiroAcessoCodigoEntrada,
    PrimeiroAcessoValidarEntrada,
    RedefinirSenhaEntrada,
    TokenPrimeiroAcessoResposta,
    TokenResposta,
)
from src.schemas.usuario import UsuarioResposta
from src.services import auth_service, usuario_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _resposta_token(usuario: Usuario) -> TokenResposta:
    return TokenResposta(
        access_token=criar_token(usuario.id, usuario.versao_token),
        expires_in=segundos_validade_token(),
        usuario=UsuarioResposta.model_validate(usuario),
    )


@router.post("/login")
def login(dados: LoginEntrada, sessao: SessaoDep) -> TokenResposta:
    try:
        usuario = auth_service.autenticar(
            sessao, dados.email, dados.senha.get_secret_value()
        )
    except auth_service.CredenciaisInvalidas:
        # Mesma resposta para e-mail inexistente, senha errada e conta bloqueada.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou muitas tentativas. "
            "Tente novamente em alguns minutos.",
        ) from None
    return _resposta_token(usuario)


@router.post("/esqueci-senha", status_code=status.HTTP_202_ACCEPTED)
def esqueci_senha(
    dados: EsqueciSenhaEntrada, sessao: SessaoDep, enviador: EnviadorEmailDep
) -> MensagemResposta:
    """Para quem já concluiu o primeiro acesso. Também reenvia o código."""
    auth_service.solicitar_codigo(sessao, enviador, dados.email)
    return MensagemResposta(
        mensagem="Se o e-mail estiver cadastrado, enviaremos um código para redefinir a senha."
    )


@router.post("/redefinir-senha", status_code=status.HTTP_204_NO_CONTENT)
def redefinir_senha(dados: RedefinirSenhaEntrada, sessao: SessaoDep) -> None:
    try:
        auth_service.redefinir_senha(
            sessao, dados.email, dados.codigo, dados.nova_senha.get_secret_value()
        )
    except auth_service.CodigoInvalido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado",
        ) from None


@router.post("/primeiro-acesso/codigo", status_code=status.HTTP_202_ACCEPTED)
def primeiro_acesso_codigo(
    dados: PrimeiroAcessoCodigoEntrada, sessao: SessaoDep, enviador: EnviadorEmailDep
) -> MensagemResposta:
    """Passo 1: envia (ou reenvia) o código para quem ainda não ativou a conta."""
    auth_service.solicitar_codigo(sessao, enviador, dados.email, primeiro_acesso=True)
    return MensagemResposta(
        mensagem="Se houver um primeiro acesso pendente para o e-mail, enviaremos um código."
    )


@router.post("/primeiro-acesso/validar-codigo")
def primeiro_acesso_validar_codigo(
    dados: PrimeiroAcessoValidarEntrada, sessao: SessaoDep
) -> TokenPrimeiroAcessoResposta:
    """Passo 2: troca o código por um token para enviar o formulário.

    O código é consumido aqui; `usuario.tipo` indica qual formulário exibir.
    """
    try:
        usuario = auth_service.validar_codigo_primeiro_acesso(
            sessao, dados.email, dados.codigo
        )
    except auth_service.CodigoInvalido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado",
        ) from None
    return TokenPrimeiroAcessoResposta(
        token_primeiro_acesso=criar_token_primeiro_acesso(
            usuario.id, usuario.versao_token
        ),
        expires_in=int(VALIDADE_TOKEN_PRIMEIRO_ACESSO.total_seconds()),
        usuario=UsuarioResposta.model_validate(usuario),
    )


@router.post("/primeiro-acesso/aluno")
def primeiro_acesso_aluno(
    dados: PrimeiroAcessoAlunoEntrada,
    usuario: UsuarioPrimeiroAcesso,
    sessao: SessaoDep,
) -> TokenResposta:
    """Passo 3 (aluno): grava o perfil e a senha, e já devolve o token de acesso.

    Exige `Authorization: Bearer <token_primeiro_acesso>`.
    """
    if usuario.tipo != TipoUsuario.ALUNO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para esta ação",
        )
    try:
        usuario_service.concluir_primeiro_acesso_aluno(
            sessao,
            usuario,
            data_nascimento=dados.data_nascimento,
            possui_responsavel=dados.possui_responsavel,
            cpf=dados.cpf,
            telefone=dados.telefone,
            responsavel_nome=dados.responsavel_nome,
            nova_senha=dados.nova_senha.get_secret_value(),
        )
    except usuario_service.PrimeiroAcessoJaConcluido:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except usuario_service.CpfJaCadastrado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado"
        ) from None
    return _resposta_token(usuario)


@router.get("/me")
def me(usuario: UsuarioAtual) -> UsuarioResposta:
    return UsuarioResposta.model_validate(usuario)


@router.post("/renovar")
def renovar(usuario: UsuarioAtual) -> TokenResposta:
    """Troca um token válido por um novo com validade cheia."""
    return _resposta_token(usuario)


@router.post("/sair-de-todos", status_code=status.HTTP_204_NO_CONTENT)
def sair_de_todos(usuario: UsuarioAtual, sessao: SessaoDep) -> None:
    auth_service.invalidar_tokens(usuario)
    sessao.commit()

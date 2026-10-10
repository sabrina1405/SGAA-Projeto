from fastapi import APIRouter, HTTPException, status

from src.api.deps import EnviadorEmailDep, ProfessorAtual, SessaoDep
from src.schemas.usuario import AlunoCriar, UsuarioResposta
from src.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("/alunos", status_code=status.HTTP_201_CREATED)
def criar_aluno(
    dados: AlunoCriar, _: ProfessorAtual, sessao: SessaoDep, enviador: EnviadorEmailDep
) -> UsuarioResposta:
    try:
        usuario = usuario_service.criar_aluno(
            sessao, enviador, nome_completo=dados.nome_completo, email=dados.email
        )
    except usuario_service.EmailJaCadastrado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado"
        ) from None
    except usuario_service.FalhaEnvioEmail:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível enviar o e-mail de acesso. Tente novamente.",
        ) from None
    return UsuarioResposta.model_validate(usuario)

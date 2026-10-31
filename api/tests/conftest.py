import os

# Valores padrão para os testes, definidos antes de importar a aplicação.
# DATABASE_URL vem do ambiente (CI) ou do .env local.
os.environ.setdefault(
    "SECRET_KEY", "chave-de-teste-com-mais-de-32-caracteres-0123456789"
)
os.environ["EMAIL_BACKEND"] = "console"

import re
from datetime import date

import pytest
from alembic.config import Config as ConfigAlembic
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from alembic import command
from src.core.config import RAIZ_API
from src.core.database import obter_engine, obter_sessao
from src.core.email import obter_enviador_email
from src.core.security import criar_token, hash_senha
from src.main import app
from src.models.aluno import Aluno
from src.models.professor import Professor
from src.models.usuario import TipoUsuario, Usuario
from src.schemas.aluno import MAIORIDADE, hoje

SENHA_PADRAO = "senha-correta-123"
CPF = "52998224725"
TELEFONE = "11912345678"
CPF_RESPONSAVEL = "11144477735"
TELEFONE_RESPONSAVEL = "11987654321"


class EnviadorEmailFalso:
    def __init__(self) -> None:
        self.mensagens: list[dict[str, str]] = []
        self.falhar = False

    def enviar(self, para: str, assunto: str, corpo: str) -> None:
        if self.falhar:
            raise RuntimeError("falha simulada no envio")
        self.mensagens.append({"para": para, "assunto": assunto, "corpo": corpo})

    def ultimo_codigo(self) -> str:
        return re.search(r"\b(\d{6})\b", self.mensagens[-1]["corpo"]).group(1)


@pytest.fixture(scope="session")
def engine():
    command.upgrade(ConfigAlembic(str(RAIZ_API / "alembic.ini")), "head")
    return obter_engine()


@pytest.fixture
def sessao(engine):
    """Sessão dentro de uma transação que é desfeita ao fim de cada teste."""
    with engine.connect() as conexao:
        transacao = conexao.begin()
        with Session(
            conexao, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as sessao:
            yield sessao
        transacao.rollback()


@pytest.fixture
def enviador():
    return EnviadorEmailFalso()


@pytest.fixture
def client(sessao, enviador):
    app.dependency_overrides[obter_sessao] = lambda: sessao
    app.dependency_overrides[obter_enviador_email] = lambda: enviador
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def criar_usuario(sessao):
    def _criar(
        email: str,
        tipo: TipoUsuario = TipoUsuario.ALUNO,
        senha: str | None = SENHA_PADRAO,
        nome_completo: str = "Usuário de Teste",
    ) -> Usuario:
        usuario = Usuario(
            nome_completo=nome_completo,
            email=email,
            tipo=tipo,
            senha=hash_senha(senha) if senha else None,
        )
        sessao.add(usuario)
        sessao.flush()
        if tipo == TipoUsuario.PROFESSOR:
            sessao.add(Professor(usuario_id=usuario.id))
        sessao.commit()
        return usuario

    return _criar


@pytest.fixture
def professor(criar_usuario):
    return criar_usuario("professora@exemplo.com", TipoUsuario.PROFESSOR)


@pytest.fixture
def outro_professor(criar_usuario):
    return criar_usuario("outra-professora@exemplo.com", TipoUsuario.PROFESSOR)


@pytest.fixture
def aluno(criar_usuario):
    return criar_usuario("aluno@exemplo.com", TipoUsuario.ALUNO)


@pytest.fixture
def criar_aluno_com_perfil(criar_usuario, sessao):
    """Aluno que já concluiu o primeiro acesso. Menor de idade ganha responsável."""

    def _criar(
        email: str,
        anos: int = 25,
        nome_completo: str = "Aluno de Teste",
        cpf: str = CPF,
    ) -> Usuario:
        usuario = criar_usuario(email, nome_completo=nome_completo)
        if anos < MAIORIDADE:
            perfil = Aluno(
                usuario_id=usuario.id,
                data_nascimento=nascido_ha(anos),
                possui_responsavel=True,
                responsavel_nome="Ana Souza",
                responsavel_cpf=CPF_RESPONSAVEL,
                responsavel_telefone=TELEFONE_RESPONSAVEL,
            )
        else:
            perfil = Aluno(
                usuario_id=usuario.id,
                data_nascimento=nascido_ha(anos),
                possui_responsavel=False,
                cpf=cpf,
                telefone=TELEFONE,
            )
        sessao.add(perfil)
        sessao.commit()
        return usuario

    return _criar


@pytest.fixture
def aluno_maior(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("maior@exemplo.com", anos=25)


@pytest.fixture
def aluno_menor(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("menor@exemplo.com", anos=15)


def nascido_ha(anos: int) -> date:
    """Data de nascimento de quem completa `anos` hoje."""
    referencia = hoje()
    try:
        return referencia.replace(year=referencia.year - anos)
    except ValueError:  # 29 de fevereiro
        return referencia.replace(year=referencia.year - anos, day=28)


def cabecalho(usuario: Usuario) -> dict[str, str]:
    token = criar_token(usuario.id, usuario.versao_token)
    return {"Authorization": f"Bearer {token}"}

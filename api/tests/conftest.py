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
from src.models.usuario import TipoUsuario, Usuario
from src.schemas.aluno import hoje

SENHA_PADRAO = "senha-correta-123"


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
        sessao.commit()
        return usuario

    return _criar


@pytest.fixture
def professor(criar_usuario):
    return criar_usuario("professora@exemplo.com", TipoUsuario.PROFESSOR)


@pytest.fixture
def aluno(criar_usuario):
    return criar_usuario("aluno@exemplo.com", TipoUsuario.ALUNO)


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

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
from src.core.drive import ArquivoNoDrive, FalhaDrive, obter_drive_na_requisicao
from src.core.email import obter_enviador_email
from src.core.push import (
    FalhaPush,
    MensagemPush,
    Recibo,
    Ticket,
    obter_enviador_push_na_requisicao,
)
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


class EnviadorPushFalso:
    """Guarda as mensagens. `erros` define o ticket de um token; `falhar` simula
    o Expo fora do ar; `recibos` responde à consulta de recibos."""

    def __init__(self) -> None:
        self.mensagens: list[MensagemPush] = []
        self.erros: dict[str, str] = {}
        self.recibos: dict[str, Recibo] = {}
        self.falhar = False
        self.consultas: list[list[str]] = []

    def enviar(self, mensagens: list[MensagemPush]) -> list[Ticket]:
        if self.falhar:
            raise FalhaPush("falha simulada no envio")
        self.mensagens.extend(mensagens)
        return [
            Ticket(ok=False, erro=self.erros[mensagem.token])
            if mensagem.token in self.erros
            else Ticket(ok=True, id=f"ticket-{mensagem.token}")
            for mensagem in mensagens
        ]

    def consultar_recibos(self, ids: list[str]) -> dict[str, Recibo]:
        self.consultas.append(ids)
        return {
            ticket_id: self.recibos[ticket_id]
            for ticket_id in ids
            if ticket_id in self.recibos
        }

    def tokens(self) -> list[str]:
        return [mensagem.token for mensagem in self.mensagens]


class DriveFalso:
    """Guarda os arquivos em memória. `falhar` simula o Drive fora do ar;
    `receber` faz o papel do app enviando o conteúdo à URL da sessão."""

    def __init__(self) -> None:
        self.sessoes: dict[int, dict] = {}
        self.arquivos: dict[str, ArquivoNoDrive] = {}
        self.compartilhados: list[str] = []
        self.apagados: list[str] = []
        self.falhar = False

    def _conferir(self) -> None:
        if self.falhar:
            raise FalhaDrive("falha simulada no Drive")

    def abrir_sessao(self, *, arquivo_id, nome, tipo_mime, tamanho, origem=None) -> str:
        self._conferir()
        self.sessoes[arquivo_id] = {
            "nome": nome,
            "tipo_mime": tipo_mime,
            "tamanho": tamanho,
            "origem": origem,
        }
        return f"https://drive.exemplo/upload/{arquivo_id}"

    def receber(self, arquivo_id, *, tamanho=None, tipo_mime=None) -> str:
        sessao = self.sessoes[arquivo_id]
        drive_file_id = f"drive-{arquivo_id}"
        self.arquivos[drive_file_id] = ArquivoNoDrive(
            id=drive_file_id,
            tamanho=sessao["tamanho"] if tamanho is None else tamanho,
            tipo_mime=tipo_mime or sessao["tipo_mime"],
            arquivo_id=str(arquivo_id),
            url=f"https://drive.exemplo/ver/{drive_file_id}",
        )
        return drive_file_id

    def obter_arquivo(self, drive_file_id):
        self._conferir()
        return self.arquivos.get(drive_file_id)

    def compartilhar_por_link(self, drive_file_id) -> None:
        self._conferir()
        self.compartilhados.append(drive_file_id)

    def apagar(self, drive_file_id) -> None:
        self._conferir()
        self.apagados.append(drive_file_id)
        self.arquivos.pop(drive_file_id, None)

    def buscar_por_arquivo_id(self, arquivo_id) -> list[str]:
        self._conferir()
        return [
            arquivo.id
            for arquivo in self.arquivos.values()
            if arquivo.arquivo_id == str(arquivo_id)
        ]


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
def enviador_push():
    return EnviadorPushFalso()


@pytest.fixture
def drive():
    return DriveFalso()


@pytest.fixture
def client(sessao, enviador, enviador_push, drive):
    app.dependency_overrides[obter_sessao] = lambda: sessao
    app.dependency_overrides[obter_enviador_email] = lambda: enviador
    app.dependency_overrides[obter_enviador_push_na_requisicao] = lambda: enviador_push
    app.dependency_overrides[obter_drive_na_requisicao] = lambda: drive
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


@pytest.fixture
def arquivo_confirmado(client, drive):
    """Faz o caminho completo do envio e devolve o id do arquivo."""

    def _enviar(usuario: Usuario, nome: str = "aula.pdf") -> int:
        resposta = client.post(
            "/v1/arquivos/sessao",
            json={"nome": nome, "tipo_mime": "application/pdf", "tamanho": 1024},
            headers=cabecalho(usuario),
        )
        assert resposta.status_code == 201, resposta.json()
        arquivo_id = resposta.json()["dados"]["arquivo_id"]
        resposta = client.post(
            f"/v1/arquivos/{arquivo_id}/confirmar",
            json={"drive_file_id": drive.receber(arquivo_id)},
            headers=cabecalho(usuario),
        )
        assert resposta.status_code == 200, resposta.json()
        return arquivo_id

    return _enviar


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

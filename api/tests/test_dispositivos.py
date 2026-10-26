import pytest
from sqlalchemy import select

from src.models.notificacao import Dispositivo
from tests.conftest import cabecalho

ROTA = "/v1/dispositivos"
TOKEN = "ExponentPushToken[abcDEF123_-]"


def _registrar(client, usuario, token=TOKEN, **campos):
    return client.post(
        ROTA, json={"token": token, **campos}, headers=cabecalho(usuario)
    )


def _dispositivo(sessao, token=TOKEN):
    return sessao.scalar(select(Dispositivo).where(Dispositivo.token == token))


@pytest.mark.parametrize(
    ("metodo", "rota", "corpo"),
    [("post", ROTA, {"token": TOKEN}), ("delete", f"{ROTA}/{TOKEN}", None)],
)
def test_dispositivos_exigem_login(client, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401


def test_registra_o_dispositivo(client, aluno_maior, sessao):
    resposta = _registrar(client, aluno_maior, plataforma="android")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "sucesso": True,
        "mensagem": "Dispositivo registrado",
        "dados": None,
    }
    dispositivo = _dispositivo(sessao)
    assert dispositivo.usuario_id == aluno_maior.id
    assert dispositivo.plataforma == "android"
    assert dispositivo.deletado_em is None


def test_professor_tambem_registra(client, professor, sessao):
    assert _registrar(client, professor, token="ExpoPushToken[xyz]").status_code == 200
    assert _dispositivo(sessao, "ExpoPushToken[xyz]").usuario_id == professor.id


@pytest.mark.parametrize(
    "campos",
    [
        {"token": ""},
        {"token": "abc"},
        {"token": "ExponentPushToken[]"},
        {"token": "ExponentPushToken[a b]"},
        {"token": "ExponentPushToken[" + "a" * 250 + "]"},
        {"token": TOKEN, "plataforma": "windows"},
        {"token": TOKEN, "usuario_id": 1},
    ],
)
def test_registro_invalido(client, aluno_maior, sessao, campos):
    resposta = client.post(ROTA, json=campos, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 422
    assert sessao.scalars(select(Dispositivo)).all() == []


def test_token_ja_registrado_passa_para_o_novo_usuario(
    client, aluno_maior, aluno_menor, sessao
):
    _registrar(client, aluno_maior)
    _registrar(client, aluno_menor)
    assert len(sessao.scalars(select(Dispositivo)).all()) == 1
    assert _dispositivo(sessao).usuario_id == aluno_menor.id


def test_remove_e_registra_de_novo(client, aluno_maior, sessao):
    _registrar(client, aluno_maior)
    resposta = client.delete(f"{ROTA}/{TOKEN}", headers=cabecalho(aluno_maior))
    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Dispositivo removido"
    assert _dispositivo(sessao).deletado_em is not None
    # Repetir a remoção não é erro.
    assert (
        client.delete(f"{ROTA}/{TOKEN}", headers=cabecalho(aluno_maior)).status_code
        == 200
    )

    _registrar(client, aluno_maior)
    assert _dispositivo(sessao).deletado_em is None


def test_nao_remove_dispositivo_de_outro_usuario(
    client, aluno_maior, aluno_menor, sessao
):
    _registrar(client, aluno_maior)
    resposta = client.delete(f"{ROTA}/{TOKEN}", headers=cabecalho(aluno_menor))
    assert resposta.status_code == 200
    assert _dispositivo(sessao).deletado_em is None


def test_sair_de_todos_remove_os_dispositivos(client, aluno_maior, sessao):
    _registrar(client, aluno_maior)
    _registrar(client, aluno_maior, token="ExpoPushToken[outro]")
    resposta = client.post("/v1/auth/sair-de-todos", headers=cabecalho(aluno_maior))
    assert resposta.status_code == 200
    ativos = sessao.scalars(
        select(Dispositivo).where(Dispositivo.deletado_em.is_(None))
    ).all()
    assert ativos == []

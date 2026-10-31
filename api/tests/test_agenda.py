from datetime import timedelta

import pytest

from src.schemas.aluno import hoje
from src.services import aula_service
from tests.conftest import cabecalho
from tests.test_aulas import _aula, _cancelar, _horario

ROTA = "/v1/agenda"


def _agenda(client, aluno, dias=(0, 61), **parametros):
    resposta = client.get(
        ROTA,
        params={
            "data_inicio": (hoje() + timedelta(days=dias[0])).isoformat(),
            "data_fim": (hoje() + timedelta(days=dias[1])).isoformat(),
            **parametros,
        },
        headers=cabecalho(aluno),
    )
    assert resposta.status_code == 200, resposta.json()
    return resposta.json()["dados"]


def _cancelar_participacao(client, aluno, aula_id, **campos):
    return client.post(
        f"{ROTA}/{aula_id}/cancelar", json=campos, headers=cabecalho(aluno)
    )


@pytest.fixture
def outro_aluno(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")


@pytest.mark.parametrize(
    ("metodo", "rota", "corpo"),
    [
        ("get", ROTA, None),
        ("get", f"{ROTA}/1", None),
        ("post", f"{ROTA}/1/cancelar", {}),
    ],
)
def test_agenda_exige_aluno(client, professor, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401
    resposta = client.request(metodo, rota, json=corpo, headers=cabecalho(professor))
    assert resposta.status_code == 403


def test_agenda_mostra_so_as_aulas_do_aluno(
    client, professor, aluno_maior, outro_aluno
):
    minha = _aula(client, professor, [aluno_maior.id], anotacoes="Só do professor")
    _aula(client, professor, [outro_aluno.id], hora=17)

    (item,) = _agenda(client, aluno_maior)
    assert item == {
        "id": minha["id"],
        "titulo": "Espanhol",
        "descricao": None,
        "inicio": _horario(3).isoformat(),
        "fim": _horario(3, hora=16).isoformat(),
        "status": "agendada",
        "participacao": "ativa",
        "motivo_cancelamento": None,
        "professor_nome": "Usuário de Teste",
    }


def test_agenda_por_periodo_e_status(client, professor, aluno_maior):
    perto = _aula(client, professor, [aluno_maior.id], dias=1)
    cancelada = _aula(client, professor, [aluno_maior.id], dias=20)
    _cancelar(client, professor, cancelada["id"], motivo="Feriado")

    assert [item["id"] for item in _agenda(client, aluno_maior, dias=(0, 5))] == [
        perto["id"]
    ]
    (item,) = _agenda(client, aluno_maior, status="cancelada")
    assert item["id"] == cancelada["id"]
    assert item["motivo_cancelamento"] == "Feriado"


def test_periodo_invalido_na_agenda(client, aluno_maior):
    resposta = client.get(
        ROTA,
        params={"data_inicio": hoje().isoformat(), "data_fim": "2000-01-01"},
        headers=cabecalho(aluno_maior),
    )
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["local"] == ["query", "data_fim"]


def test_detalhe_so_da_propria_aula(client, professor, aluno_maior, outro_aluno):
    aula = _aula(client, professor, [aluno_maior.id])
    rota = f"{ROTA}/{aula['id']}"
    resposta = client.get(rota, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["id"] == aula["id"]
    assert client.get(rota, headers=cabecalho(outro_aluno)).status_code == 404


def test_aluno_cancela_a_participacao(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = _cancelar_participacao(client, aluno_maior, aula["id"], motivo="Viagem")
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["status"] == "agendada"
    assert dados["participacao"] == "cancelada"

    resposta = _cancelar_participacao(client, aluno_maior, aula["id"])
    assert resposta.status_code == 409
    assert resposta.json()["mensagem"] == "Você já cancelou esta aula"


def test_aluno_nao_cancela_aula_alheia(client, professor, aluno_maior, outro_aluno):
    aula = _aula(client, professor, [aluno_maior.id])
    assert _cancelar_participacao(client, outro_aluno, aula["id"]).status_code == 404


def test_aluno_nao_cancela_aula_cancelada(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    _cancelar(client, professor, aula["id"])
    assert _cancelar_participacao(client, aluno_maior, aula["id"]).status_code == 409


def test_aluno_nao_cancela_aula_que_comecou(
    client, professor, aluno_maior, monkeypatch
):
    aula = _aula(client, professor, [aluno_maior.id])
    momento = _horario(3) + timedelta(minutes=1)
    monkeypatch.setattr(aula_service, "agora", lambda: momento)
    assert _cancelar_participacao(client, aluno_maior, aula["id"]).status_code == 409

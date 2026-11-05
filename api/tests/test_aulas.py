from datetime import UTC, datetime, time, timedelta

import pytest

from src.schemas.aluno import HORARIO_DE_BRASILIA, hoje
from src.services import aula_service
from tests.conftest import cabecalho

ROTA = "/v1/aulas"
ROTA_REPOSICOES = f"{ROTA}/reposicoes-pendentes"


def _horario(dias: int, hora: int = 15, minuto: int = 0) -> datetime:
    return datetime.combine(
        hoje() + timedelta(days=dias), time(hora, minuto, tzinfo=HORARIO_DE_BRASILIA)
    )


def _criar(client, professor, aluno_ids=(), dias=3, hora=15, duracao=60, **campos):
    inicio = _horario(dias, hora)
    dados = {
        "titulo": "Espanhol",
        "inicio": inicio.isoformat(),
        "fim": (inicio + timedelta(minutes=duracao)).isoformat(),
        "aluno_ids": list(aluno_ids),
        **campos,
    }
    return client.post(ROTA, json=dados, headers=cabecalho(professor))


def _aula(client, professor, aluno_ids=(), **campos):
    resposta = _criar(client, professor, aluno_ids, **campos)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()["dados"]


def _listar(client, professor, dias=(0, 61), **parametros):
    resposta = client.get(
        ROTA,
        params={
            "data_inicio": (hoje() + timedelta(days=dias[0])).isoformat(),
            "data_fim": (hoje() + timedelta(days=dias[1])).isoformat(),
            **parametros,
        },
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 200, resposta.json()
    return resposta.json()["dados"]


def _detalhe(client, professor, aula_id):
    resposta = client.get(f"{ROTA}/{aula_id}", headers=cabecalho(professor))
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _editar(client, professor, aula_id, escopo=None, **campos):
    params = {"escopo": escopo} if escopo else None
    return client.patch(
        f"{ROTA}/{aula_id}", json=campos, params=params, headers=cabecalho(professor)
    )


def _cancelar(client, professor, aula_id, escopo=None, **campos):
    params = {"escopo": escopo} if escopo else None
    return client.post(
        f"{ROTA}/{aula_id}/cancelar",
        json=campos,
        params=params,
        headers=cabecalho(professor),
    )


def _reposicoes(client, professor):
    resposta = client.get(ROTA_REPOSICOES, headers=cabecalho(professor))
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _grupo(client, professor, aluno_ids=()):
    resposta = client.post(
        "/v1/grupos",
        json={"titulo": "Turma A", "aluno_ids": list(aluno_ids)},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 201
    return resposta.json()["dados"]["id"]


def _tipos_de_erro(resposta):
    assert resposta.status_code == 422, resposta.json()
    return [(erro["local"], erro["tipo"]) for erro in resposta.json()["erros"]]


def _ids(aulas):
    return [aula["id"] for aula in aulas]


@pytest.fixture
def outro_aluno(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")


@pytest.fixture
def avancar(monkeypatch):
    """Simula o relógio no futuro."""

    def _avancar(momento):
        monkeypatch.setattr(aula_service, "agora", lambda: momento)

    return _avancar


CHAMADAS_PROFESSOR = [
    ("post", ROTA, {"titulo": "Espanhol"}),
    ("get", ROTA, None),
    ("get", ROTA_REPOSICOES, None),
    ("delete", f"{ROTA_REPOSICOES}/1/2", None),
    ("get", f"{ROTA}/1", None),
    ("patch", f"{ROTA}/1", {"titulo": "Inglês"}),
    ("post", f"{ROTA}/1/cancelar", {}),
    ("post", f"{ROTA}/1/alunos", {"aluno_ids": [1]}),
    ("delete", f"{ROTA}/1/alunos/2", None),
]


@pytest.mark.parametrize(("metodo", "rota", "corpo"), CHAMADAS_PROFESSOR)
def test_aulas_exigem_professor(client, aluno_maior, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401
    resposta = client.request(metodo, rota, json=corpo, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 403


# --- criação ---


def test_cria_aula(client, professor, aluno_maior):
    aula = _aula(
        client,
        professor,
        [aluno_maior.id],
        descricao="Aula individual",
        anotacoes="Revisar o pretérito",
    )
    assert aula["titulo"] == "Espanhol"
    assert aula["descricao"] == "Aula individual"
    assert aula["anotacoes"] == "Revisar o pretérito"
    assert aula["status"] == "agendada"
    assert aula["serie_id"] is None
    assert aula["inicio"] == _horario(3).isoformat()
    assert aula["inicio"].endswith("-03:00")
    assert [aluno["id"] for aluno in aula["alunos"]] == [aluno_maior.id]
    assert aula["alunos"][0]["status"] == "ativa"
    assert aula["grupos"] == []


def test_horario_em_outro_fuso_e_convertido(client, professor, aluno_maior):
    em_utc = _horario(3).astimezone(UTC)
    aula = _aula(
        client,
        professor,
        [aluno_maior.id],
        inicio=em_utc.isoformat(),
        fim=(em_utc + timedelta(hours=1)).isoformat(),
    )
    assert aula["inicio"] == _horario(3).isoformat()


def test_horario_sem_fuso_e_recusado(client, professor, aluno_maior):
    resposta = _criar(client, professor, [aluno_maior.id], inicio="2030-01-10T15:00:00")
    assert (["body", "inicio"], "timezone_aware") in _tipos_de_erro(resposta)


def test_grupo_vira_alunos_da_aula(client, professor, aluno_maior, outro_aluno):
    grupo_id = _grupo(client, professor, [aluno_maior.id, outro_aluno.id])
    aula = _aula(client, professor, [aluno_maior.id], grupo_ids=[grupo_id])
    assert sorted(aluno["id"] for aluno in aula["alunos"]) == sorted(
        [aluno_maior.id, outro_aluno.id]
    )
    assert [grupo["id"] for grupo in aula["grupos"]] == [grupo_id]


def test_quem_entra_no_grupo_depois_nao_entra_na_aula(
    client, professor, aluno_maior, outro_aluno
):
    grupo_id = _grupo(client, professor, [aluno_maior.id])
    aula = _aula(client, professor, grupo_ids=[grupo_id])
    client.post(
        f"/v1/grupos/{grupo_id}/alunos",
        json={"aluno_ids": [outro_aluno.id]},
        headers=cabecalho(professor),
    )
    alunos = _detalhe(client, professor, aula["id"])["alunos"]
    assert [aluno["id"] for aluno in alunos] == [aluno_maior.id]


def test_aula_sem_aluno(client, professor):
    grupo_vazio = _grupo(client, professor)
    for campos in ({}, {"grupo_ids": [grupo_vazio]}):
        resposta = _criar(client, professor, **campos)
        assert (["body", "aluno_ids"], "sem_aluno") in _tipos_de_erro(resposta)


def test_aluno_e_grupo_invalidos(client, professor, outro_professor, aluno):
    resposta = _criar(client, professor, [aluno.id])
    assert _tipos_de_erro(resposta) == [(["body", "aluno_ids"], "aluno_invalido")]

    grupo_alheio = _grupo(client, outro_professor)
    resposta = _criar(client, professor, grupo_ids=[grupo_alheio])
    assert _tipos_de_erro(resposta) == [(["body", "grupo_ids"], "grupo_invalido")]


@pytest.mark.parametrize(
    ("campos", "campo"),
    [
        ({"duracao": 0}, "fim"),
        ({"duracao": -30}, "fim"),
        ({"duracao": 12 * 60 + 1}, "fim"),
        ({"dias": -1}, "inicio"),
    ],
)
def test_horario_invalido(client, professor, aluno_maior, campos, campo):
    resposta = _criar(client, professor, [aluno_maior.id], **campos)
    assert _tipos_de_erro(resposta) == [(["body", campo], "horario_invalido")]


def test_aula_de_12_horas_e_aceita(client, professor, aluno_maior):
    _aula(client, professor, [aluno_maior.id], hora=8, duracao=12 * 60)


# --- repetição semanal ---


def test_repeticao_semanal_cria_as_aulas_da_serie(client, professor, aluno_maior):
    repetir_ate = (hoje() + timedelta(days=3, weeks=3)).isoformat()
    aula = _aula(
        client,
        professor,
        [aluno_maior.id],
        repetir_semanalmente=True,
        repetir_ate=repetir_ate,
    )
    assert aula["serie_id"] == aula["id"]
    aulas = _listar(client, professor)
    assert [item["inicio"] for item in aulas] == [
        _horario(3 + 7 * semana).isoformat() for semana in range(4)
    ]
    assert {item["serie_id"] for item in aulas} == {aula["id"]}
    assert all(item["alunos"][0]["id"] == aluno_maior.id for item in aulas)


@pytest.mark.parametrize(
    "campos",
    [
        {"repetir_semanalmente": True},
        {"repetir_semanalmente": True, "repetir_ate": hoje().isoformat()},
        {
            "repetir_semanalmente": True,
            "repetir_ate": (hoje() + timedelta(days=4, weeks=26)).isoformat(),
        },
        {"repetir_ate": (hoje() + timedelta(weeks=2)).isoformat()},
    ],
)
def test_repeticao_invalida(client, professor, aluno_maior, campos):
    resposta = _criar(client, professor, [aluno_maior.id], **campos)
    assert _tipos_de_erro(resposta) == [(["body", "repetir_ate"], "repeticao_invalida")]


# --- conflito de horário ---


def test_aulas_sobrepostas_geram_conflito(client, professor, aluno_maior):
    _aula(client, professor, [aluno_maior.id], hora=15)
    resposta = _criar(client, professor, [aluno_maior.id], hora=14, duracao=90)
    assert resposta.status_code == 409
    assert resposta.json()["mensagem"].startswith('Conflito com a aula "Espanhol" de ')


def test_aulas_encostadas_nao_conflitam(client, professor, aluno_maior):
    _aula(client, professor, [aluno_maior.id], hora=15)
    _aula(client, professor, [aluno_maior.id], hora=16)
    _aula(client, professor, [aluno_maior.id], hora=14)


def test_conflito_em_uma_ocorrencia_da_serie(client, professor, aluno_maior):
    _aula(client, professor, [aluno_maior.id], dias=17)
    resposta = _criar(
        client,
        professor,
        [aluno_maior.id],
        repetir_semanalmente=True,
        repetir_ate=(hoje() + timedelta(weeks=4)).isoformat(),
    )
    assert resposta.status_code == 409
    assert len(_listar(client, professor)) == 1


def test_conflito_ignora_outro_professor_e_aula_cancelada(
    client, professor, outro_professor, aluno_maior
):
    _aula(client, outro_professor, [aluno_maior.id])
    aula = _aula(client, professor, [aluno_maior.id])
    _cancelar(client, professor, aula["id"])
    _aula(client, professor, [aluno_maior.id])


# --- listagem e detalhe ---


def test_lista_por_periodo(client, professor, outro_professor, aluno_maior):
    perto = _aula(client, professor, [aluno_maior.id], dias=1)
    longe = _aula(client, professor, [aluno_maior.id], dias=40)
    _aula(client, outro_professor, [aluno_maior.id], dias=1)
    assert _ids(_listar(client, professor)) == [perto["id"], longe["id"]]
    assert _ids(_listar(client, professor, dias=(1, 1))) == [perto["id"]]
    assert _ids(_listar(client, professor, dias=(2, 39))) == []


def test_periodo_considera_o_dia_em_brasilia(client, professor, aluno_maior):
    # 23h30 em Brasília já é o dia seguinte em UTC.
    aula = _aula(client, professor, [aluno_maior.id], dias=2, hora=23, duracao=20)
    assert _ids(_listar(client, professor, dias=(2, 2))) == [aula["id"]]
    assert _ids(_listar(client, professor, dias=(3, 3))) == []


def test_filtros_da_listagem(client, professor, aluno_maior, outro_aluno):
    grupo_id = _grupo(client, professor, [outro_aluno.id])
    do_aluno = _aula(client, professor, [aluno_maior.id], hora=9)
    do_grupo = _aula(client, professor, grupo_ids=[grupo_id], hora=11)
    cancelada = _aula(client, professor, [aluno_maior.id], hora=13)
    _cancelar(client, professor, cancelada["id"])

    assert _ids(_listar(client, professor, aluno_id=aluno_maior.id)) == [
        do_aluno["id"],
        cancelada["id"],
    ]
    assert _ids(_listar(client, professor, grupo_id=grupo_id)) == [do_grupo["id"]]
    assert _ids(_listar(client, professor, status="cancelada")) == [cancelada["id"]]
    assert _ids(_listar(client, professor, status="agendada")) == [
        do_aluno["id"],
        do_grupo["id"],
    ]


def test_item_da_listagem(client, professor, aluno_maior, outro_aluno):
    _aula(client, professor, [aluno_maior.id, outro_aluno.id])
    (item,) = _listar(client, professor)
    assert set(item) == {
        "id",
        "titulo",
        "inicio",
        "fim",
        "status",
        "serie_id",
        "alunos",
    }
    assert [aluno["nome_completo"] for aluno in item["alunos"]] == [
        "Aluno de Teste",
        "Bia",
    ]


@pytest.mark.parametrize(("inicio", "fim"), [(5, 4), (0, 62)])
def test_periodo_invalido(client, professor, inicio, fim):
    resposta = client.get(
        ROTA,
        params={
            "data_inicio": (hoje() + timedelta(days=inicio)).isoformat(),
            "data_fim": (hoje() + timedelta(days=fim)).isoformat(),
        },
        headers=cabecalho(professor),
    )
    assert _tipos_de_erro(resposta) == [(["query", "data_fim"], "periodo_invalido")]


def test_listagem_exige_o_periodo(client, professor):
    resposta = client.get(ROTA, headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_aula_de_outro_professor_nao_aparece(
    client, professor, outro_professor, aluno_maior
):
    aula = _aula(client, outro_professor, [aluno_maior.id])
    rota = f"{ROTA}/{aula['id']}"
    assert client.get(rota, headers=cabecalho(professor)).status_code == 404
    assert _editar(client, professor, aula["id"], titulo="X").status_code == 404
    assert _cancelar(client, professor, aula["id"]).status_code == 404


# --- edição ---


def test_edita_os_campos_enviados(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id], descricao="Individual")
    resposta = _editar(client, professor, aula["id"], titulo="Inglês", descricao=None)
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["titulo"] == "Inglês"
    assert dados["descricao"] is None
    assert dados["inicio"] == aula["inicio"]


@pytest.mark.parametrize("corpo", [{}, {"titulo": None}, {"inicio": None}])
def test_edicao_invalida(client, professor, aluno_maior, corpo):
    aula = _aula(client, professor, [aluno_maior.id])
    assert _editar(client, professor, aula["id"], **corpo).status_code == 422


def _serie(client, professor, aluno_maior, semanas=3):
    _aula(
        client,
        professor,
        [aluno_maior.id],
        repetir_semanalmente=True,
        repetir_ate=(hoje() + timedelta(days=3, weeks=semanas)).isoformat(),
    )
    return _listar(client, professor)


def test_edita_so_esta_aula_da_serie(client, professor, aluno_maior):
    serie = _serie(client, professor, aluno_maior)
    _editar(client, professor, serie[1]["id"], titulo="Conversação")
    titulos = [item["titulo"] for item in _listar(client, professor)]
    assert titulos == ["Espanhol", "Conversação", "Espanhol", "Espanhol"]


def test_edita_esta_e_as_seguintes(client, professor, aluno_maior):
    serie = _serie(client, professor, aluno_maior)
    _cancelar(client, professor, serie[3]["id"])
    novo_inicio = _horario(3 + 7, hora=16)
    resposta = _editar(
        client,
        professor,
        serie[1]["id"],
        escopo="esta_e_seguintes",
        titulo="Conversação",
        inicio=novo_inicio.isoformat(),
        fim=(novo_inicio + timedelta(minutes=90)).isoformat(),
    )
    assert resposta.status_code == 200
    aulas = _listar(client, professor)
    assert [item["titulo"] for item in aulas] == [
        "Espanhol",
        "Conversação",
        "Conversação",
        "Espanhol",
    ]
    assert [item["inicio"] for item in aulas] == [
        _horario(3).isoformat(),
        _horario(10, hora=16).isoformat(),
        _horario(17, hora=16).isoformat(),
        _horario(24).isoformat(),  # cancelada: fica como estava
    ]
    assert (
        aulas[2]["fim"] == (_horario(17, hora=16) + timedelta(minutes=90)).isoformat()
    )


def test_mudar_horario_com_conflito_nao_altera_nada(client, professor, aluno_maior):
    serie = _serie(client, professor, aluno_maior)
    _aula(client, professor, [aluno_maior.id], dias=17, hora=17)
    resposta = _editar(
        client,
        professor,
        serie[0]["id"],
        escopo="esta_e_seguintes",
        inicio=_horario(3, hora=17).isoformat(),
        fim=_horario(3, hora=18).isoformat(),
    )
    assert resposta.status_code == 409
    assert _listar(client, professor)[0]["inicio"] == _horario(3).isoformat()


def test_mudar_para_o_proprio_horario_nao_conflita(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = _editar(
        client,
        professor,
        aula["id"],
        fim=(_horario(3) + timedelta(minutes=30)).isoformat(),
    )
    assert resposta.status_code == 200


def test_mudar_horario_para_o_passado(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = _editar(
        client,
        professor,
        aula["id"],
        inicio=_horario(-1).isoformat(),
        fim=_horario(-1, hora=16).isoformat(),
    )
    assert _tipos_de_erro(resposta) == [(["body", "inicio"], "horario_invalido")]


def test_marcar_realizada(client, professor, aluno_maior, avancar):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = _editar(client, professor, aula["id"], status="realizada")
    assert _tipos_de_erro(resposta) == [(["body", "status"], "status_invalido")]

    avancar(_horario(3) + timedelta(minutes=10))
    resposta = _editar(client, professor, aula["id"], status="realizada")
    assert resposta.json()["dados"]["status"] == "realizada"
    resposta = _editar(client, professor, aula["id"], inicio=_horario(5).isoformat())
    assert resposta.status_code == 409


def test_status_nao_vale_para_a_serie(client, professor, aluno_maior):
    serie = _serie(client, professor, aluno_maior)
    resposta = _editar(
        client, professor, serie[0]["id"], escopo="esta_e_seguintes", status="agendada"
    )
    assert _tipos_de_erro(resposta) == [(["body", "status"], "escopo_invalido")]


def test_status_cancelada_tem_rota_propria(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    assert _editar(client, professor, aula["id"], status="cancelada").status_code == 422


def test_aula_cancelada_nao_pode_ser_editada(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    _cancelar(client, professor, aula["id"])
    resposta = _editar(client, professor, aula["id"], titulo="Inglês")
    assert resposta.status_code == 409
    assert resposta.json()["mensagem"] == "Aula cancelada não pode ser alterada"


# --- cancelamento ---


def test_cancela_a_aula(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = _cancelar(client, professor, aula["id"], motivo="Imprevisto")
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["status"] == "cancelada"
    assert dados["motivo_cancelamento"] == "Imprevisto"
    assert _reposicoes(client, professor)["total"] == 0

    resposta = _cancelar(client, professor, aula["id"])
    assert resposta.status_code == 409


def test_cancela_esta_e_as_seguintes(client, professor, aluno_maior):
    serie = _serie(client, professor, aluno_maior)
    _cancelar(client, professor, serie[2]["id"], escopo="esta_e_seguintes")
    status = [item["status"] for item in _listar(client, professor)]
    assert status == ["agendada", "agendada", "cancelada", "cancelada"]


def test_cancelar_com_reposicao(client, professor, aluno_maior, outro_aluno):
    aula = _aula(client, professor, [aluno_maior.id, outro_aluno.id])
    _cancelar(client, professor, aula["id"], motivo="Fiquei doente", repor=True)
    pendentes = _reposicoes(client, professor)
    assert pendentes["total"] == 2
    assert {item["aluno_id"] for item in pendentes["itens"]} == {
        aluno_maior.id,
        outro_aluno.id,
    }
    assert pendentes["itens"][0]["cancelada_por"] == "professor"
    assert pendentes["itens"][0]["motivo_cancelamento"] == "Fiquei doente"


# --- alunos da aula ---


def test_adiciona_e_remove_alunos(client, professor, aluno_maior, outro_aluno):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = client.post(
        f"{ROTA}/{aula['id']}/alunos",
        json={"aluno_ids": [aluno_maior.id, outro_aluno.id]},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 200
    assert len(resposta.json()["dados"]["alunos"]) == 2

    rota = f"{ROTA}/{aula['id']}/alunos/{outro_aluno.id}"
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 200
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 404
    alunos = _detalhe(client, professor, aula["id"])["alunos"]
    assert [aluno["id"] for aluno in alunos] == [aluno_maior.id]


def test_adiciona_aluno_nas_seguintes(client, professor, aluno_maior, outro_aluno):
    serie = _serie(client, professor, aluno_maior)
    client.post(
        f"{ROTA}/{serie[2]['id']}/alunos",
        params={"escopo": "esta_e_seguintes"},
        json={"aluno_ids": [outro_aluno.id]},
        headers=cabecalho(professor),
    )
    totais = [len(item["alunos"]) for item in _listar(client, professor)]
    assert totais == [1, 1, 2, 2]


def test_adicionar_exige_aluno_ou_grupo(client, professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    resposta = client.post(
        f"{ROTA}/{aula['id']}/alunos", json={}, headers=cabecalho(professor)
    )
    assert resposta.status_code == 422


# --- reposição ---


def _aluno_cancela(client, aluno, aula_id, motivo="Consulta médica"):
    resposta = client.post(
        f"/v1/agenda/{aula_id}/cancelar",
        json={"motivo": motivo},
        headers=cabecalho(aluno),
    )
    assert resposta.status_code == 200


def test_fluxo_de_reposicao(client, professor, aluno_maior, outro_aluno):
    aula = _aula(client, professor, [aluno_maior.id, outro_aluno.id])
    _aluno_cancela(client, aluno_maior, aula["id"])

    pendentes = _reposicoes(client, professor)
    assert pendentes["total"] == 1
    (item,) = pendentes["itens"]
    assert item["aula_id"] == aula["id"]
    assert item["aluno_id"] == aluno_maior.id
    assert item["cancelada_por"] == "aluno"
    assert item["motivo_cancelamento"] == "Consulta médica"
    # A aula segue para os demais.
    detalhe = _detalhe(client, professor, aula["id"])
    assert detalhe["status"] == "agendada"
    assert {aluno["id"]: aluno["status"] for aluno in detalhe["alunos"]} == {
        aluno_maior.id: "cancelada",
        outro_aluno.id: "ativa",
    }

    reposicao = _aula(
        client, professor, [aluno_maior.id], dias=5, reposicao_de_aula_id=aula["id"]
    )
    assert reposicao["reposicao_de_aula_id"] == aula["id"]
    assert _reposicoes(client, professor)["total"] == 0


def test_reposicao_de_aula_alheia(client, professor, outro_professor, aluno_maior):
    alheia = _aula(client, outro_professor, [aluno_maior.id])
    resposta = _criar(
        client, professor, [aluno_maior.id], reposicao_de_aula_id=alheia["id"]
    )
    assert _tipos_de_erro(resposta) == [
        (["body", "reposicao_de_aula_id"], "aula_invalida")
    ]


def test_dispensar_reposicao(client, professor, outro_professor, aluno_maior):
    aula = _aula(client, professor, [aluno_maior.id])
    _aluno_cancela(client, aluno_maior, aula["id"])
    rota = f"{ROTA_REPOSICOES}/{aula['id']}/{aluno_maior.id}"

    assert client.delete(rota, headers=cabecalho(outro_professor)).status_code == 404
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 200
    assert _reposicoes(client, professor)["total"] == 0
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 404


def test_formatar_horario():
    momento = datetime(2026, 9, 24, 18, 0, tzinfo=UTC)
    assert aula_service.formatar_horario(momento) == "qui, 24/09 às 15:00"

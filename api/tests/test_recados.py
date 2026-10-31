from datetime import UTC, datetime, timedelta

import pytest

from src.models.recado import Recado, RecadoAluno, RecadoGeral
from src.schemas.aluno import hoje
from tests.conftest import cabecalho

ROTA = "/v1/recados"
ROTA_GERAL = f"{ROTA}/geral"
ROTA_MURAL = "/v1/mural"
TEXTO = "Queridos alunos, **bem-vindos**!\n\nLink: meet.jit.si/ElCaminoIdiomas"


def _dia(deslocamento: int) -> str:
    return (hoje() + timedelta(days=deslocamento)).isoformat()


def _criar(client, professor, **campos):
    dados = {"conteudo": TEXTO, "todos_alunos": True, **campos}
    return client.post(ROTA, json=dados, headers=cabecalho(professor))


def _recado(client, professor, **campos):
    resposta = _criar(client, professor, **campos)
    assert resposta.status_code == 201
    return resposta.json()["dados"]


def _editar(client, professor, recado_id, **campos):
    return client.patch(
        f"{ROTA}/{recado_id}", json=campos, headers=cabecalho(professor)
    )


def _listar(client, professor, **parametros):
    resposta = client.get(ROTA, params=parametros, headers=cabecalho(professor))
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _mural(client, aluno, **parametros):
    resposta = client.get(ROTA_MURAL, params=parametros, headers=cabecalho(aluno))
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _ids_no_mural(client, aluno):
    return [item["id"] for item in _mural(client, aluno)["itens"]]


def _grupo(client, professor, aluno_ids=()):
    resposta = client.post(
        "/v1/grupos",
        json={"titulo": "Turma A", "aluno_ids": list(aluno_ids)},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 201
    return resposta.json()["dados"]["id"]


def _tipos_de_erro(resposta):
    assert resposta.status_code == 422
    return [(erro["local"], erro["tipo"]) for erro in resposta.json()["erros"]]


def _erro(mensagem):
    return {"sucesso": False, "mensagem": mensagem, "dados": None}


CHAMADAS_PROFESSOR = [
    ("get", ROTA_GERAL, None),
    ("put", ROTA_GERAL, {"conteudo": TEXTO}),
    ("delete", ROTA_GERAL, None),
    ("post", ROTA, {"conteudo": TEXTO, "todos_alunos": True}),
    ("get", ROTA, None),
    ("get", f"{ROTA}/1", None),
    ("patch", f"{ROTA}/1", {"conteudo": TEXTO}),
    ("delete", f"{ROTA}/1", None),
]


@pytest.mark.parametrize(("metodo", "rota", "corpo"), CHAMADAS_PROFESSOR)
def test_recados_exigem_professor(client, aluno_maior, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401
    resposta = client.request(metodo, rota, json=corpo, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 403


@pytest.mark.parametrize("rota", [ROTA_MURAL, f"{ROTA_MURAL}/geral"])
def test_mural_exige_aluno(client, professor, rota):
    assert client.get(rota).status_code == 401
    assert client.get(rota, headers=cabecalho(professor)).status_code == 403


# --- recado geral ---


def test_painel_comeca_vazio(client, professor):
    resposta = client.get(ROTA_GERAL, headers=cabecalho(professor))
    assert resposta.status_code == 200
    assert resposta.json() == {
        "sucesso": True,
        "mensagem": "Recado geral vazio",
        "dados": None,
    }


def test_salva_e_edita_o_recado_geral(client, professor, sessao):
    resposta = client.put(
        ROTA_GERAL, json={"conteudo": f"  {TEXTO}  "}, headers=cabecalho(professor)
    )
    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Recado geral salvo"
    assert resposta.json()["dados"]["conteudo"] == TEXTO

    client.put(ROTA_GERAL, json={"conteudo": "Novo"}, headers=cabecalho(professor))
    dados = client.get(ROTA_GERAL, headers=cabecalho(professor)).json()["dados"]
    assert dados["conteudo"] == "Novo"
    assert sessao.query(RecadoGeral).count() == 1


def test_limpa_e_reaproveita_o_recado_geral(client, professor, sessao):
    client.put(ROTA_GERAL, json={"conteudo": TEXTO}, headers=cabecalho(professor))

    resposta = client.delete(ROTA_GERAL, headers=cabecalho(professor))
    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Recado geral limpo"
    assert client.get(ROTA_GERAL, headers=cabecalho(professor)).json()["dados"] is None
    assert sessao.get(RecadoGeral, professor.id).deletado_em is not None
    # Limpar de novo não é erro.
    assert client.delete(ROTA_GERAL, headers=cabecalho(professor)).status_code == 200

    client.put(ROTA_GERAL, json={"conteudo": "Voltou"}, headers=cabecalho(professor))
    registro = sessao.get(RecadoGeral, professor.id)
    assert registro.deletado_em is None
    assert registro.conteudo == "Voltou"


def test_cada_professor_tem_o_proprio_painel(client, professor, outro_professor):
    client.put(ROTA_GERAL, json={"conteudo": TEXTO}, headers=cabecalho(professor))
    resposta = client.get(ROTA_GERAL, headers=cabecalho(outro_professor))
    assert resposta.json()["dados"] is None


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"conteudo": ""},
        {"conteudo": "  \n "},
        {"conteudo": None},
        {"conteudo": "a" * 5001},
        {"conteudo": "texto\x00nulo"},
        {"conteudo": TEXTO, "professor_id": 1},
    ],
)
def test_recado_geral_invalido(client, professor, sessao, corpo):
    resposta = client.put(ROTA_GERAL, json=corpo, headers=cabecalho(professor))
    assert resposta.status_code == 422
    assert sessao.query(RecadoGeral).count() == 0


def test_aluno_ve_os_recados_gerais_preenchidos(
    client, professor, outro_professor, aluno_maior
):
    client.put(ROTA_GERAL, json={"conteudo": TEXTO}, headers=cabecalho(professor))
    client.put(
        ROTA_GERAL, json={"conteudo": "Outro"}, headers=cabecalho(outro_professor)
    )
    client.delete(ROTA_GERAL, headers=cabecalho(outro_professor))

    resposta = client.get(f"{ROTA_MURAL}/geral", headers=cabecalho(aluno_maior))
    assert resposta.status_code == 200
    itens = resposta.json()["dados"]
    assert [(item["professor_nome"], item["conteudo"]) for item in itens] == [
        ("Usuário de Teste", TEXTO)
    ]


# --- criação ---


def test_cria_recado_para_todos_os_alunos(client, professor, sessao):
    resposta = _criar(client, professor, data_fim=_dia(7))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["mensagem"] == "Recado criado"
    dados = corpo["dados"]
    assert dados == {
        "id": dados["id"],
        "conteudo": TEXTO,
        "data_inicio": _dia(0),
        "data_fim": _dia(7),
        "todos_alunos": True,
        "todos_grupos": False,
        "alunos": [],
        "grupos": [],
        "criado_em": dados["criado_em"],
    }
    assert sessao.get(Recado, dados["id"]).professor_id == professor.id


def test_cria_recado_para_alunos_e_grupos(client, professor, aluno_maior, aluno_menor):
    grupo_id = _grupo(client, professor, [aluno_menor.id])
    dados = _recado(
        client,
        professor,
        todos_alunos=False,
        aluno_ids=[aluno_maior.id],
        grupo_ids=[grupo_id],
        data_inicio=_dia(2),
    )
    assert [aluno["id"] for aluno in dados["alunos"]] == [aluno_maior.id]
    assert dados["grupos"] == [{"id": grupo_id, "titulo": "Turma A"}]
    assert dados["data_inicio"] == _dia(2)
    assert dados["data_fim"] is None


def test_conteudo_mantem_quebras_de_linha_e_markdown(client, professor):
    dados = _recado(client, professor, conteudo="  # Aviso\r\n\n- item\t1  ")
    assert dados["conteudo"] == "# Aviso\n\n- item\t1"


@pytest.mark.parametrize(
    "campos",
    [
        {"conteudo": ""},
        {"conteudo": "a" * 5001},
        {"conteudo": "a\x07b"},
        {"data_inicio": "31/12/2026"},
        {"data_fim": "amanhã"},
        {"todos_alunos": "talvez"},
        {"todos_alunos": False, "aluno_ids": [0]},
        {"todos_alunos": False, "grupo_ids": [1, 1]},
        {"todos_alunos": False, "aluno_ids": list(range(1, 102))},
        {"professor_id": 1},
    ],
)
def test_criacao_invalida(client, professor, sessao, campos):
    assert _criar(client, professor, **campos).status_code == 422
    assert sessao.query(Recado).count() == 0


def test_data_de_fim_antes_do_inicio(client, professor, sessao):
    resposta = _criar(client, professor, data_inicio=_dia(3), data_fim=_dia(2))
    assert _tipos_de_erro(resposta) == [(["body", "data_fim"], "periodo_invalido")]
    assert sessao.query(Recado).count() == 0


def test_inicio_e_fim_no_mesmo_dia(client, professor):
    dados = _recado(client, professor, data_inicio=_dia(1), data_fim=_dia(1))
    assert dados["data_fim"] == _dia(1)


def test_recado_sem_destinatario(client, professor, sessao):
    resposta = _criar(client, professor, todos_alunos=False)
    assert _tipos_de_erro(resposta) == [
        (["body", "aluno_ids"], "sem_destinatario"),
        (["body", "grupo_ids"], "sem_destinatario"),
    ]
    assert sessao.query(Recado).count() == 0


def test_todos_com_destinatarios_avulsos(client, professor, aluno_maior):
    grupo_id = _grupo(client, professor)
    resposta = _criar(client, professor, aluno_ids=[aluno_maior.id])
    assert _tipos_de_erro(resposta) == [
        (["body", "aluno_ids"], "destinatarios_conflitantes")
    ]
    resposta = _criar(
        client, professor, todos_alunos=False, todos_grupos=True, grupo_ids=[grupo_id]
    )
    assert _tipos_de_erro(resposta) == [
        (["body", "grupo_ids"], "destinatarios_conflitantes")
    ]


def test_criacao_com_aluno_invalido(client, professor, aluno, aluno_maior, sessao):
    # `aluno` não concluiu o primeiro acesso.
    resposta = _criar(
        client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id, aluno.id]
    )
    assert resposta.status_code == 422
    assert resposta.json()["erros"] == [
        {
            "local": ["body", "aluno_ids"],
            "tipo": "aluno_invalido",
            "mensagem": f"aluno não encontrado: {aluno.id}",
        }
    ]
    assert sessao.query(Recado).count() == 0


def test_criacao_com_grupo_de_outro_professor(
    client, professor, outro_professor, sessao
):
    alheio = _grupo(client, outro_professor)
    excluido = _grupo(client, professor)
    client.delete(f"/v1/grupos/{excluido}", headers=cabecalho(professor))

    resposta = _criar(
        client, professor, todos_alunos=False, grupo_ids=[alheio, excluido]
    )
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["mensagem"] == (
        f"grupo não encontrado: {alheio}, {excluido}"
    )
    assert sessao.query(Recado).count() == 0


# --- histórico ---


def test_historico_vazio(client, professor):
    assert _listar(client, professor) == {"itens": [], "total": 0}


def test_historico_do_mais_novo_ao_mais_antigo(
    client, professor, aluno_maior, aluno_menor
):
    grupo_id = _grupo(client, professor, [aluno_menor.id])
    primeiro = _recado(client, professor)
    segundo = _recado(
        client,
        professor,
        todos_alunos=False,
        aluno_ids=[aluno_maior.id, aluno_menor.id],
        grupo_ids=[grupo_id],
    )

    dados = _listar(client, professor)
    assert dados["total"] == 2
    assert [item["id"] for item in dados["itens"]] == [segundo["id"], primeiro["id"]]
    item = dados["itens"][0]
    assert item == {
        "id": segundo["id"],
        "conteudo": TEXTO,
        "data_inicio": _dia(0),
        "data_fim": None,
        "todos_alunos": False,
        "todos_grupos": False,
        "total_alunos": 2,
        "total_grupos": 1,
        "criado_em": item["criado_em"],
    }


def test_paginacao_do_historico(client, professor):
    ids = [_recado(client, professor)["id"] for _ in range(3)]
    pagina = _listar(client, professor, pagina=2, tamanho=2)
    assert pagina["total"] == 3
    assert [item["id"] for item in pagina["itens"]] == [ids[0]]


@pytest.mark.parametrize(
    "parametros", [{"pagina": 0}, {"tamanho": 0}, {"tamanho": 101}]
)
def test_parametros_invalidos_no_historico(client, professor, parametros):
    resposta = client.get(ROTA, params=parametros, headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_cada_professor_so_ve_os_proprios_recados(client, professor, outro_professor):
    recado = _recado(client, professor)
    assert _listar(client, outro_professor)["total"] == 0
    for metodo, corpo in [
        ("get", None),
        ("patch", {"conteudo": "x"}),
        ("delete", None),
    ]:
        resposta = client.request(
            metodo,
            f"{ROTA}/{recado['id']}",
            json=corpo,
            headers=cabecalho(outro_professor),
        )
        assert resposta.status_code == 404
        assert resposta.json() == _erro("Recado não encontrado")


@pytest.mark.parametrize("recado_id", ["0", "-1", "abc", "2147483648"])
def test_detalhe_com_id_invalido(client, professor, recado_id):
    resposta = client.get(f"{ROTA}/{recado_id}", headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_detalhe_omite_aluno_e_grupo_removidos(
    client, professor, aluno_maior, aluno_menor, sessao
):
    grupo_id = _grupo(client, professor)
    recado = _recado(
        client,
        professor,
        todos_alunos=False,
        aluno_ids=[aluno_maior.id, aluno_menor.id],
        grupo_ids=[grupo_id],
    )
    aluno_maior.deletado_em = datetime.now(UTC)
    sessao.commit()
    client.delete(f"/v1/grupos/{grupo_id}", headers=cabecalho(professor))

    resposta = client.get(f"{ROTA}/{recado['id']}", headers=cabecalho(professor))
    dados = resposta.json()["dados"]
    assert [aluno["id"] for aluno in dados["alunos"]] == [aluno_menor.id]
    assert dados["grupos"] == []


# --- edição ---


def test_edita_o_conteudo_e_preserva_o_resto(client, professor, aluno_maior):
    recado = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])
    resposta = _editar(client, professor, recado["id"], conteudo="Novo texto")
    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Recado atualizado"
    dados = resposta.json()["dados"]
    assert dados["conteudo"] == "Novo texto"
    assert [aluno["id"] for aluno in dados["alunos"]] == [aluno_maior.id]


def test_edicao_troca_os_destinatarios(
    client, professor, aluno_maior, aluno_menor, sessao
):
    grupo_id = _grupo(client, professor)
    recado = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])
    resposta = _editar(
        client,
        professor,
        recado["id"],
        aluno_ids=[aluno_menor.id],
        grupo_ids=[grupo_id],
    )
    dados = resposta.json()["dados"]
    assert [aluno["id"] for aluno in dados["alunos"]] == [aluno_menor.id]
    assert [grupo["id"] for grupo in dados["grupos"]] == [grupo_id]
    assert sessao.get(RecadoAluno, (recado["id"], aluno_maior.id)) is None

    resposta = _editar(client, professor, recado["id"], aluno_ids=[], todos_alunos=True)
    assert resposta.json()["dados"]["alunos"] == []
    assert resposta.json()["dados"]["todos_alunos"] is True


def test_edicao_do_texto_com_aluno_removido_do_sistema(
    client, professor, aluno_maior, sessao
):
    recado = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])
    aluno_maior.deletado_em = datetime.now(UTC)
    sessao.commit()
    resposta = _editar(client, professor, recado["id"], conteudo="Ainda vale")
    assert resposta.status_code == 200


def test_edicao_tira_a_data_de_fim(client, professor):
    recado = _recado(client, professor, data_fim=_dia(3))
    resposta = _editar(client, professor, recado["id"], data_fim=None)
    assert resposta.json()["dados"]["data_fim"] is None


def test_edicao_confere_o_periodo_com_o_que_esta_salvo(client, professor, sessao):
    recado = _recado(client, professor, data_inicio=_dia(2))
    resposta = _editar(client, professor, recado["id"], data_fim=_dia(1))
    assert _tipos_de_erro(resposta) == [(["body", "data_fim"], "periodo_invalido")]
    assert sessao.get(Recado, recado["id"]).data_fim is None


def test_edicao_que_deixa_o_recado_sem_destinatario(
    client, professor, aluno_maior, sessao
):
    recado = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])
    resposta = _editar(client, professor, recado["id"], aluno_ids=[])
    assert _tipos_de_erro(resposta)[0][1] == "sem_destinatario"
    assert sessao.get(RecadoAluno, (recado["id"], aluno_maior.id)) is not None


@pytest.mark.parametrize(
    "campos",
    [
        {},
        {"conteudo": None},
        {"data_inicio": None},
        {"todos_alunos": None},
        {"aluno_ids": None},
        {"conteudo": ""},
        {"professor_id": 1},
    ],
)
def test_edicao_invalida(client, professor, campos):
    recado = _recado(client, professor)
    assert _editar(client, professor, recado["id"], **campos).status_code == 422


# --- exclusão ---


def test_exclui_o_recado(client, professor, aluno_maior, sessao):
    recado = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])
    resposta = client.delete(f"{ROTA}/{recado['id']}", headers=cabecalho(professor))
    assert resposta.status_code == 200
    assert resposta.json() == {
        "sucesso": True,
        "mensagem": "Recado excluído",
        "dados": None,
    }
    assert _listar(client, professor)["total"] == 0
    assert _ids_no_mural(client, aluno_maior) == []
    assert sessao.get(Recado, recado["id"]).deletado_em is not None
    assert sessao.get(RecadoAluno, (recado["id"], aluno_maior.id)) is not None

    resposta = client.delete(f"{ROTA}/{recado['id']}", headers=cabecalho(professor))
    assert resposta.status_code == 404


# --- mural do aluno ---


def test_mural_mostra_o_recado_ao_aluno(client, professor, aluno_maior):
    recado = _recado(client, professor, data_fim=_dia(0))
    dados = _mural(client, aluno_maior)
    assert dados == {
        "itens": [
            {
                "id": recado["id"],
                "conteudo": TEXTO,
                "data_inicio": _dia(0),
                "data_fim": _dia(0),
                "professor_nome": "Usuário de Teste",
                "criado_em": recado["criado_em"],
            }
        ],
        "total": 1,
    }


def test_mural_respeita_o_periodo(client, professor, aluno_maior):
    _recado(client, professor, data_inicio=_dia(1))
    _recado(client, professor, data_inicio=_dia(-5), data_fim=_dia(-1))
    sem_fim = _recado(client, professor, data_inicio=_dia(-30))
    assert _ids_no_mural(client, aluno_maior) == [sem_fim["id"]]


def test_mural_por_destinatario(
    client, professor, outro_professor, aluno_maior, aluno_menor, criar_aluno_com_perfil
):
    fora = criar_aluno_com_perfil("fora@exemplo.com", anos=16)
    grupo_id = _grupo(client, professor, [aluno_menor.id])
    _grupo(client, outro_professor, [fora.id])

    direto = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])
    por_grupo = _recado(client, professor, todos_alunos=False, grupo_ids=[grupo_id])
    todos_grupos = _recado(client, professor, todos_alunos=False, todos_grupos=True)
    todos = _recado(client, professor)

    assert _ids_no_mural(client, aluno_maior) == [todos["id"], direto["id"]]
    assert _ids_no_mural(client, aluno_menor) == [
        todos["id"],
        todos_grupos["id"],
        por_grupo["id"],
    ]
    # Está só no grupo de outro professor.
    assert _ids_no_mural(client, fora) == [todos["id"]]


def test_mural_ignora_grupo_excluido_e_aluno_que_saiu(
    client, professor, aluno_maior, aluno_menor
):
    grupo_id = _grupo(client, professor, [aluno_maior.id, aluno_menor.id])
    _recado(client, professor, todos_alunos=False, grupo_ids=[grupo_id])
    _recado(client, professor, todos_alunos=False, todos_grupos=True)

    client.delete(
        f"/v1/grupos/{grupo_id}/alunos/{aluno_menor.id}", headers=cabecalho(professor)
    )
    assert _ids_no_mural(client, aluno_menor) == []
    assert len(_ids_no_mural(client, aluno_maior)) == 2

    client.delete(f"/v1/grupos/{grupo_id}", headers=cabecalho(professor))
    assert _ids_no_mural(client, aluno_maior) == []


def test_mural_por_data_de_inicio_mais_recente(client, professor, aluno_maior):
    antigo = _recado(client, professor, data_inicio=_dia(-3))
    recente = _recado(client, professor, data_inicio=_dia(-1))
    assert _ids_no_mural(client, aluno_maior) == [recente["id"], antigo["id"]]


def test_paginacao_do_mural(client, professor, aluno_maior):
    ids = [_recado(client, professor)["id"] for _ in range(3)]
    dados = _mural(client, aluno_maior, pagina=2, tamanho=2)
    assert dados["total"] == 3
    assert [item["id"] for item in dados["itens"]] == [ids[0]]

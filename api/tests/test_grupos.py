from datetime import UTC, datetime

import pytest

from src.models.grupo import Grupo, GrupoAluno
from tests.conftest import TELEFONE, TELEFONE_RESPONSAVEL, cabecalho

ROTA = "/v1/grupos"


def _criar(client, professor, **campos):
    dados = {"titulo": "Turma A", **campos}
    return client.post(ROTA, json=dados, headers=cabecalho(professor))


def _grupo(client, professor, **campos):
    resposta = _criar(client, professor, **campos)
    assert resposta.status_code == 201
    return resposta.json()["dados"]


def _detalhe(client, professor, grupo_id):
    resposta = client.get(f"{ROTA}/{grupo_id}", headers=cabecalho(professor))
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _listar(client, professor, **parametros):
    resposta = client.get(ROTA, params=parametros, headers=cabecalho(professor))
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _ids(dados):
    return [aluno["id"] for aluno in dados["alunos"]]


def _erro(mensagem):
    return {"sucesso": False, "mensagem": mensagem, "dados": None}


CHAMADAS = [
    ("post", ROTA, {"titulo": "Turma A"}),
    ("get", ROTA, None),
    ("get", f"{ROTA}/1", None),
    ("patch", f"{ROTA}/1", {"titulo": "Turma B"}),
    ("delete", f"{ROTA}/1", None),
    ("post", f"{ROTA}/1/alunos", {"aluno_ids": [1]}),
    ("delete", f"{ROTA}/1/alunos/1", None),
]


@pytest.mark.parametrize(("metodo", "rota", "corpo"), CHAMADAS)
def test_grupos_exigem_professor(client, aluno_maior, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401
    resposta = client.request(metodo, rota, json=corpo, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 403


# --- criação ---


def test_cria_grupo_so_com_o_titulo(client, professor, sessao):
    resposta = _criar(client, professor, titulo="  Turma   de Sábado ")
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["sucesso"] is True
    assert corpo["mensagem"] == "Grupo criado"
    dados = corpo["dados"]
    assert dados == {
        "id": dados["id"],
        "titulo": "Turma de Sábado",
        "descricao": None,
        "alunos": [],
    }
    assert sessao.get(Grupo, dados["id"]).professor_id == professor.id


def test_cria_grupo_com_descricao_e_alunos(client, professor, aluno_maior, aluno_menor):
    dados = _grupo(
        client,
        professor,
        descricao="Aulas de terça",
        aluno_ids=[aluno_menor.id, aluno_maior.id],
    )
    assert dados["descricao"] == "Aulas de terça"
    por_id = {aluno["id"]: aluno for aluno in dados["alunos"]}
    assert por_id[aluno_maior.id] == {
        "id": aluno_maior.id,
        "nome_completo": "Aluno de Teste",
        "email": "maior@exemplo.com",
        "telefone": TELEFONE,
    }
    assert por_id[aluno_menor.id]["telefone"] == TELEFONE_RESPONSAVEL


@pytest.mark.parametrize(
    "campos",
    [
        {"titulo": ""},
        {"titulo": "   "},
        {"titulo": "a" * 51},
        {"titulo": None},
        {"descricao": ""},
        {"descricao": "a" * 101},
        {"aluno_ids": [0]},
        {"aluno_ids": ["abc"]},
        {"aluno_ids": list(range(1, 102))},
        {"professor_id": 1},
    ],
)
def test_criacao_invalida(client, professor, sessao, campos):
    assert _criar(client, professor, **campos).status_code == 422
    assert sessao.query(Grupo).count() == 0


def test_criacao_sem_titulo(client, professor):
    resposta = client.post(ROTA, json={}, headers=cabecalho(professor))
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["local"] == ["body", "titulo"]


def test_criacao_com_aluno_invalido_nao_cria_o_grupo(
    client, professor, criar_usuario, aluno_maior, sessao
):
    convidado = criar_usuario("convidado@exemplo.com", senha=None)
    invalidos = [convidado.id, professor.id, aluno_maior.id + 1000]

    resposta = _criar(client, professor, aluno_ids=[aluno_maior.id, *invalidos])
    assert resposta.status_code == 422
    erro = resposta.json()["erros"][0]
    assert erro["local"] == ["body", "aluno_ids"]
    assert erro["tipo"] == "aluno_invalido"
    for aluno_id in invalidos:
        assert str(aluno_id) in erro["mensagem"]
    assert sessao.query(Grupo).count() == 0


def test_criacao_recusa_aluno_repetido(client, professor, aluno_maior):
    resposta = _criar(client, professor, aluno_ids=[aluno_maior.id, aluno_maior.id])
    assert resposta.status_code == 422


def test_aluno_removido_do_sistema_nao_entra_em_grupo(
    client, professor, aluno_maior, sessao
):
    aluno_maior.deletado_em = datetime.now(UTC)
    sessao.commit()
    assert _criar(client, professor, aluno_ids=[aluno_maior.id]).status_code == 422


# --- listagem ---


def test_listagem_vazia(client, professor):
    assert _listar(client, professor) == {"itens": [], "total": 0}


def test_listagem_em_ordem_de_titulo_com_total_de_alunos(
    client, professor, aluno_maior, aluno_menor
):
    _grupo(client, professor, titulo="beta", aluno_ids=[aluno_maior.id])
    _grupo(client, professor, titulo="Álgebra", descricao="Terça")
    _grupo(
        client, professor, titulo="Cálculo", aluno_ids=[aluno_maior.id, aluno_menor.id]
    )

    dados = _listar(client, professor)
    assert dados["total"] == 3
    resumo = [
        (item["titulo"], item["descricao"], item["total_alunos"])
        for item in dados["itens"]
    ]
    assert resumo == [("Álgebra", "Terça", 0), ("beta", None, 1), ("Cálculo", None, 2)]
    assert set(dados["itens"][0]) == {"id", "titulo", "descricao", "total_alunos"}


def test_paginacao_dos_grupos(client, professor):
    for indice in range(5):
        _grupo(client, professor, titulo=f"Grupo {indice}")

    primeira = _listar(client, professor, tamanho=2)
    terceira = _listar(client, professor, tamanho=2, pagina=3)
    assert [item["titulo"] for item in primeira["itens"]] == ["Grupo 0", "Grupo 1"]
    assert [item["titulo"] for item in terceira["itens"]] == ["Grupo 4"]
    assert _listar(client, professor, tamanho=2, pagina=4) == {"itens": [], "total": 5}
    assert primeira["total"] == terceira["total"] == 5


@pytest.mark.parametrize(
    "parametros", [{"tamanho": 0}, {"tamanho": 101}, {"pagina": 0}, {"pagina": 501}]
)
def test_parametros_invalidos_na_listagem(client, professor, parametros):
    resposta = client.get(ROTA, params=parametros, headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_titulos_repetidos_sao_permitidos(client, professor):
    primeiro = _grupo(client, professor)
    segundo = _grupo(client, professor)
    assert primeiro["id"] != segundo["id"]
    assert _listar(client, professor)["total"] == 2


def test_cada_professor_so_ve_os_proprios_grupos(client, professor, outro_professor):
    grupo = _grupo(client, professor)
    rota = f"{ROTA}/{grupo['id']}"
    headers = cabecalho(outro_professor)

    assert _listar(client, outro_professor) == {"itens": [], "total": 0}
    respostas = [
        client.get(rota, headers=headers),
        client.patch(rota, json={"titulo": "Invadido"}, headers=headers),
        client.delete(rota, headers=headers),
        client.post(f"{rota}/alunos", json={"aluno_ids": [1]}, headers=headers),
        client.delete(f"{rota}/alunos/1", headers=headers),
    ]
    for resposta in respostas:
        assert resposta.status_code == 404
        assert resposta.json() == _erro("Grupo não encontrado")
    assert _detalhe(client, professor, grupo["id"])["titulo"] == "Turma A"


# --- detalhe ---


def test_detalhe_lista_os_alunos_em_ordem_alfabetica(
    client, professor, criar_aluno_com_perfil
):
    ids = [
        criar_aluno_com_perfil(f"a{indice}@exemplo.com", anos=15, nome_completo=nome).id
        for indice, nome in enumerate(["Érica", "bruno", "Ana"])
    ]
    grupo = _grupo(client, professor, aluno_ids=ids)

    dados = _detalhe(client, professor, grupo["id"])
    assert [aluno["nome_completo"] for aluno in dados["alunos"]] == [
        "Ana",
        "bruno",
        "Érica",
    ]


def test_aluno_removido_do_sistema_some_do_grupo(
    client, professor, aluno_maior, aluno_menor, sessao
):
    grupo = _grupo(client, professor, aluno_ids=[aluno_maior.id, aluno_menor.id])
    aluno_maior.deletado_em = datetime.now(UTC)
    sessao.commit()

    assert _ids(_detalhe(client, professor, grupo["id"])) == [aluno_menor.id]
    assert _listar(client, professor)["itens"][0]["total_alunos"] == 1


@pytest.mark.parametrize("grupo_id", ["0", "-1", "abc", "2147483648"])
def test_detalhe_com_id_invalido(client, professor, grupo_id):
    resposta = client.get(f"{ROTA}/{grupo_id}", headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_detalhe_de_grupo_inexistente(client, professor):
    resposta = client.get(f"{ROTA}/999999", headers=cabecalho(professor))
    assert resposta.status_code == 404
    assert resposta.json() == _erro("Grupo não encontrado")


# --- edição ---


def test_edita_o_titulo_e_preserva_o_resto(client, professor, aluno_maior):
    grupo = _grupo(
        client, professor, descricao="Aulas de terça", aluno_ids=[aluno_maior.id]
    )
    resposta = client.patch(
        f"{ROTA}/{grupo['id']}",
        json={"titulo": "  Turma   B "},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Grupo atualizado"
    dados = resposta.json()["dados"]
    assert dados["titulo"] == "Turma B"
    assert dados["descricao"] == "Aulas de terça"
    assert _ids(dados) == [aluno_maior.id]
    assert _detalhe(client, professor, grupo["id"]) == dados


def test_edita_e_apaga_a_descricao(client, professor):
    grupo = _grupo(client, professor)
    rota = f"{ROTA}/{grupo['id']}"
    headers = cabecalho(professor)

    resposta = client.patch(rota, json={"descricao": "Nova"}, headers=headers)
    assert resposta.json()["dados"]["descricao"] == "Nova"
    assert resposta.json()["dados"]["titulo"] == "Turma A"

    resposta = client.patch(rota, json={"descricao": None}, headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["descricao"] is None


@pytest.mark.parametrize(
    "campos",
    [
        {},
        {"titulo": None},
        {"titulo": ""},
        {"titulo": "a" * 51},
        {"descricao": "a" * 101},
        {"aluno_ids": [1]},
        {"professor_id": 1},
    ],
)
def test_edicao_invalida(client, professor, campos):
    grupo = _grupo(client, professor, descricao="Original")
    resposta = client.patch(
        f"{ROTA}/{grupo['id']}", json=campos, headers=cabecalho(professor)
    )
    assert resposta.status_code == 422
    dados = _detalhe(client, professor, grupo["id"])
    assert (dados["titulo"], dados["descricao"]) == ("Turma A", "Original")


# --- exclusão ---


def test_exclui_o_grupo(client, professor, aluno_maior, sessao):
    grupo = _grupo(client, professor, aluno_ids=[aluno_maior.id])
    rota = f"{ROTA}/{grupo['id']}"
    headers = cabecalho(professor)

    resposta = client.delete(rota, headers=headers)
    assert resposta.status_code == 200
    assert resposta.json() == {
        "sucesso": True,
        "mensagem": "Grupo excluído",
        "dados": None,
    }

    assert _listar(client, professor) == {"itens": [], "total": 0}
    assert client.get(rota, headers=headers).status_code == 404
    assert client.delete(rota, headers=headers).status_code == 404
    assert client.patch(rota, json={"titulo": "X"}, headers=headers).status_code == 404

    # Soft delete: o grupo e os vínculos continuam no banco.
    assert sessao.get(Grupo, grupo["id"]).deletado_em is not None
    assert sessao.get(GrupoAluno, (grupo["id"], aluno_maior.id)) is not None


# --- alunos do grupo ---


def _adicionar(client, professor, grupo_id, aluno_ids):
    return client.post(
        f"{ROTA}/{grupo_id}/alunos",
        json={"aluno_ids": aluno_ids},
        headers=cabecalho(professor),
    )


def test_adiciona_alunos_depois_da_criacao(client, professor, aluno_maior, aluno_menor):
    grupo = _grupo(client, professor)

    resposta = _adicionar(client, professor, grupo["id"], [aluno_maior.id])
    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Alunos adicionados"
    assert _ids(resposta.json()["dados"]) == [aluno_maior.id]

    # Quem já está no grupo é ignorado.
    resposta = _adicionar(
        client, professor, grupo["id"], [aluno_maior.id, aluno_menor.id]
    )
    assert resposta.status_code == 200
    assert sorted(_ids(resposta.json()["dados"])) == sorted(
        [aluno_maior.id, aluno_menor.id]
    )
    assert _listar(client, professor)["itens"][0]["total_alunos"] == 2


def test_adicao_com_aluno_invalido_nao_adiciona_nenhum(client, professor, aluno_maior):
    grupo = _grupo(client, professor)
    resposta = _adicionar(
        client, professor, grupo["id"], [aluno_maior.id, aluno_maior.id + 1000]
    )
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["local"] == ["body", "aluno_ids"]
    assert _detalhe(client, professor, grupo["id"])["alunos"] == []


@pytest.mark.parametrize("aluno_ids", [[], [0], [1, 1], "1", list(range(1, 102))])
def test_adicao_invalida(client, professor, aluno_ids):
    grupo = _grupo(client, professor)
    resposta = _adicionar(client, professor, grupo["id"], aluno_ids)
    assert resposta.status_code == 422


def test_adicao_em_grupo_inexistente(client, professor, aluno_maior):
    resposta = _adicionar(client, professor, 999999, [aluno_maior.id])
    assert resposta.status_code == 404


def test_o_mesmo_aluno_pode_estar_em_varios_grupos(client, professor, aluno_maior):
    primeiro = _grupo(client, professor, titulo="A", aluno_ids=[aluno_maior.id])
    segundo = _grupo(client, professor, titulo="B", aluno_ids=[aluno_maior.id])
    assert _ids(_detalhe(client, professor, primeiro["id"])) == [aluno_maior.id]
    assert _ids(_detalhe(client, professor, segundo["id"])) == [aluno_maior.id]


def test_remove_aluno_do_grupo(client, professor, aluno_maior, aluno_menor):
    grupo = _grupo(client, professor, aluno_ids=[aluno_maior.id, aluno_menor.id])
    outro = _grupo(client, professor, titulo="B", aluno_ids=[aluno_maior.id])
    rota = f"{ROTA}/{grupo['id']}/alunos/{aluno_maior.id}"
    headers = cabecalho(professor)

    resposta = client.delete(rota, headers=headers)
    assert resposta.status_code == 200
    assert resposta.json() == {
        "sucesso": True,
        "mensagem": "Aluno removido do grupo",
        "dados": None,
    }
    assert _ids(_detalhe(client, professor, grupo["id"])) == [aluno_menor.id]
    # Sai só deste grupo.
    assert _ids(_detalhe(client, professor, outro["id"])) == [aluno_maior.id]

    resposta = client.delete(rota, headers=headers)
    assert resposta.status_code == 404
    assert resposta.json() == _erro("Aluno não está no grupo")

    # Pode voltar depois.
    assert (
        _adicionar(client, professor, grupo["id"], [aluno_maior.id]).status_code == 200
    )

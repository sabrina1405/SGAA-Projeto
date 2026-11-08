import pytest

from tests.conftest import cabecalho
from tests.test_atividades import _grupo
from tests.test_pastas import _pasta

ROTA = "/v1/meus-materiais"


@pytest.fixture
def outro_aluno(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")


def _ids(client, aluno):
    resposta = client.get(ROTA, headers=cabecalho(aluno))
    assert resposta.status_code == 200
    return [item["id"] for item in resposta.json()["dados"]["itens"]]


def _detalhe(client, aluno, pasta_id):
    return client.get(f"{ROTA}/{pasta_id}", headers=cabecalho(aluno))


def test_rotas_sao_do_aluno(client, professor):
    for rota in (ROTA, f"{ROTA}/1"):
        assert client.get(rota).status_code == 401
        assert client.get(rota, headers=cabecalho(professor)).status_code == 403


def test_visibilidade_por_destinatario(client, professor, aluno_maior, outro_aluno):
    grupo_id = _grupo(client, professor, [aluno_maior.id])
    sem_destinatario = _pasta(client, professor, "Rascunho")
    todos = _pasta(client, professor, "Todos", todos_alunos=True)
    grupos = _pasta(client, professor, "Grupos", todos_grupos=True)
    do_grupo = _pasta(client, professor, "Do grupo", grupo_ids=[grupo_id])
    avulso = _pasta(client, professor, "Avulso", aluno_ids=[outro_aluno.id])

    assert _ids(client, aluno_maior) == [do_grupo["id"], grupos["id"], todos["id"]]
    assert _ids(client, outro_aluno) == [avulso["id"], todos["id"]]
    assert _detalhe(client, aluno_maior, sem_destinatario["id"]).status_code == 404
    assert _detalhe(client, aluno_maior, avulso["id"]).status_code == 404


def test_subpasta_herda_da_raiz(
    client, professor, aluno_maior, outro_aluno, arquivo_confirmado
):
    raiz = _pasta(client, professor, aluno_ids=[aluno_maior.id])
    filha = _pasta(client, professor, "Módulo 1", pasta_pai_id=raiz["id"])
    arquivo_id = arquivo_confirmado(professor, "apostila.pdf")
    client.post(
        f"/v1/pastas/{filha['id']}/arquivos",
        json={"arquivo_ids": [arquivo_id]},
        headers=cabecalho(professor),
    )

    detalhe = _detalhe(client, aluno_maior, raiz["id"]).json()["dados"]
    assert [item["nome"] for item in detalhe["subpastas"]] == ["Módulo 1"]
    detalhe = _detalhe(client, aluno_maior, filha["id"]).json()["dados"]
    assert detalhe["professor_nome"] == professor.nome_completo
    assert [item["nome"] for item in detalhe["caminho"]] == ["Apostilas", "Módulo 1"]
    assert detalhe["arquivos"][0]["url"].startswith("https://")
    # A subpasta não aparece na lista de raízes, e outro aluno não a vê.
    assert _ids(client, aluno_maior) == [raiz["id"]]
    assert _detalhe(client, outro_aluno, filha["id"]).status_code == 404


def test_sair_do_grupo_revoga_o_acesso(client, professor, aluno_maior):
    grupo_id = _grupo(client, professor, [aluno_maior.id])
    pasta = _pasta(client, professor, grupo_ids=[grupo_id])
    assert _ids(client, aluno_maior) == [pasta["id"]]
    client.delete(
        f"/v1/grupos/{grupo_id}/alunos/{aluno_maior.id}", headers=cabecalho(professor)
    )
    assert _ids(client, aluno_maior) == []
    assert _detalhe(client, aluno_maior, pasta["id"]).status_code == 404


def test_todos_grupos_so_alcanca_os_grupos_do_professor(
    client, professor, outro_professor, aluno_maior
):
    _grupo(client, outro_professor, [aluno_maior.id])
    _pasta(client, professor, todos_grupos=True)
    assert _ids(client, aluno_maior) == []


def test_pasta_excluida_some(client, professor, aluno_maior):
    pasta = _pasta(client, professor, todos_alunos=True)
    filha = _pasta(client, professor, "Filha", pasta_pai_id=pasta["id"])
    client.delete(f"/v1/pastas/{pasta['id']}", headers=cabecalho(professor))
    assert _ids(client, aluno_maior) == []
    assert _detalhe(client, aluno_maior, filha["id"]).status_code == 404


def test_mover_para_outra_raiz_muda_quem_ve(
    client, professor, aluno_maior, outro_aluno
):
    da_turma = _pasta(client, professor, "Turma", aluno_ids=[aluno_maior.id])
    de_outra = _pasta(client, professor, "Outra", aluno_ids=[outro_aluno.id])
    filha = _pasta(client, professor, "Filha", pasta_pai_id=da_turma["id"])
    client.patch(
        f"/v1/pastas/{filha['id']}",
        json={"pasta_pai_id": de_outra["id"]},
        headers=cabecalho(professor),
    )
    assert _detalhe(client, aluno_maior, filha["id"]).status_code == 404
    assert _detalhe(client, outro_aluno, filha["id"]).status_code == 200

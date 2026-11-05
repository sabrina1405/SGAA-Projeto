import pytest

from src.models.aluno import Aluno
from tests.conftest import (
    CPF,
    CPF_RESPONSAVEL,
    TELEFONE,
    TELEFONE_RESPONSAVEL,
    cabecalho,
    nascido_ha,
)

ROTA = "/v1/auth/me/perfil"
OUTRO_CPF = "39053344705"


def _editar(client, usuario, **campos):
    return client.patch(ROTA, json=campos, headers=cabecalho(usuario))


def _campos_recusados(resposta):
    assert resposta.status_code == 422
    return [item["local"] for item in resposta.json()["erros"]]


def test_perfil_exige_autenticacao(client):
    assert client.get(ROTA).status_code == 401
    assert client.patch(ROTA, json={"telefone": TELEFONE}).status_code == 401


def test_perfil_e_so_para_aluno(client, professor):
    assert client.get(ROTA, headers=cabecalho(professor)).status_code == 403
    assert _editar(client, professor, nome_completo="Outro Nome").status_code == 403


def test_aluno_sem_perfil(client, aluno):
    resposta = client.get(ROTA, headers=cabecalho(aluno))
    assert resposta.status_code == 404
    assert resposta.json() == {
        "sucesso": False,
        "mensagem": "Perfil não encontrado",
        "dados": None,
    }
    assert _editar(client, aluno, nome_completo="Outro Nome").status_code == 404


def test_perfil_de_aluno_maior_de_idade(client, aluno_maior):
    resposta = client.get(ROTA, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 200
    assert resposta.json()["dados"] == {
        "id": aluno_maior.id,
        "nome_completo": "Aluno de Teste",
        "email": "maior@exemplo.com",
        "perfil": {
            "data_nascimento": nascido_ha(25).isoformat(),
            "possui_responsavel": False,
            "cpf": CPF,
            "telefone": TELEFONE,
            "responsavel_nome": None,
            "responsavel_cpf": None,
            "responsavel_telefone": None,
        },
    }


def test_perfil_de_aluno_com_responsavel(client, aluno_menor):
    resposta = client.get(ROTA, headers=cabecalho(aluno_menor))
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["perfil"] == {
        "data_nascimento": nascido_ha(15).isoformat(),
        "possui_responsavel": True,
        "cpf": None,
        "telefone": None,
        "responsavel_nome": "Ana Souza",
        "responsavel_cpf": CPF_RESPONSAVEL,
        "responsavel_telefone": TELEFONE_RESPONSAVEL,
    }


def test_me_continua_sem_os_dados_do_perfil(client, aluno_maior):
    resposta = client.get("/v1/auth/me", headers=cabecalho(aluno_maior))
    assert set(resposta.json()["dados"]) == {"id", "nome_completo", "email", "tipo"}


def test_aluno_maior_edita_nome_e_telefone(client, aluno_maior, sessao):
    resposta = _editar(
        client,
        aluno_maior,
        nome_completo="  Novo   Nome ",
        telefone="(21) 99876-5432",
    )
    assert resposta.status_code == 200
    corpo = resposta.json()["dados"]
    assert corpo["nome_completo"] == "Novo Nome"
    assert corpo["perfil"]["telefone"] == "21998765432"
    assert corpo["perfil"]["cpf"] == CPF

    assert client.get(ROTA, headers=cabecalho(aluno_maior)).json()["dados"] == corpo
    me = client.get("/v1/auth/me", headers=cabecalho(aluno_maior))
    assert me.json()["dados"]["nome_completo"] == "Novo Nome"
    assert sessao.get(Aluno, aluno_maior.id).telefone == "21998765432"


def test_edicao_parcial_preserva_os_outros_campos(client, aluno_menor, sessao):
    resposta = _editar(client, aluno_menor, responsavel_telefone="21998765432")
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["nome_completo"] == "Aluno de Teste"

    perfil = sessao.get(Aluno, aluno_menor.id)
    assert perfil.responsavel_telefone == "21998765432"
    assert perfil.responsavel_nome == "Ana Souza"
    assert perfil.responsavel_cpf == CPF_RESPONSAVEL


def test_aluno_troca_de_responsavel(client, aluno_menor):
    resposta = _editar(
        client,
        aluno_menor,
        responsavel_nome="Carlos Souza",
        responsavel_cpf="390.533.447-05",
        responsavel_telefone="21 3456-7890",
    )
    assert resposta.status_code == 200
    perfil = resposta.json()["dados"]["perfil"]
    assert perfil["responsavel_nome"] == "Carlos Souza"
    assert perfil["responsavel_cpf"] == OUTRO_CPF
    assert perfil["responsavel_telefone"] == "2134567890"
    assert perfil["cpf"] is None
    assert perfil["telefone"] is None


def test_aluno_maior_nao_edita_dados_de_responsavel(client, aluno_maior, sessao):
    resposta = _editar(
        client,
        aluno_maior,
        nome_completo="Novo Nome",
        responsavel_nome="Ana Souza",
        responsavel_cpf=OUTRO_CPF,
    )
    assert _campos_recusados(resposta) == [
        ["body", "responsavel_nome"],
        ["body", "responsavel_cpf"],
    ]
    assert resposta.json()["erros"][0]["tipo"] == "campo_nao_permitido"

    # O pedido é recusado por inteiro: o nome, que era válido, não muda.
    sessao.refresh(aluno_maior)
    assert aluno_maior.nome_completo == "Aluno de Teste"
    assert sessao.get(Aluno, aluno_maior.id).responsavel_nome is None


def test_aluno_com_responsavel_nao_edita_o_proprio_telefone(
    client, aluno_menor, sessao
):
    resposta = _editar(client, aluno_menor, telefone=TELEFONE)
    assert _campos_recusados(resposta) == [["body", "telefone"]]
    assert sessao.get(Aluno, aluno_menor.id).telefone is None


def test_quem_fez_18_continua_com_os_dados_do_responsavel(client, aluno_menor, sessao):
    perfil = sessao.get(Aluno, aluno_menor.id)
    perfil.data_nascimento = nascido_ha(19)
    sessao.commit()

    assert _editar(client, aluno_menor, telefone=TELEFONE).status_code == 422
    resposta = _editar(client, aluno_menor, responsavel_nome="Carlos Souza")
    assert resposta.status_code == 200


@pytest.mark.parametrize(
    "campos",
    [
        {"email": "novo@exemplo.com"},
        {"cpf": OUTRO_CPF},
        {"data_nascimento": "2000-01-01"},
        {"possui_responsavel": True},
        {"senha": "Senha-Nova-1!"},
        {"tipo": "professor"},
    ],
)
def test_campos_bloqueados_no_perfil(client, aluno_maior, campos):
    resposta = _editar(client, aluno_maior, telefone=TELEFONE, **campos)
    assert _campos_recusados(resposta) == [["body", *campos]]


@pytest.mark.parametrize(
    "campos",
    [
        {},
        {"telefone": None},
        {"nome_completo": None},
        {"nome_completo": "ab"},
        {"telefone": "123"},
    ],
)
def test_edicao_invalida_de_aluno_maior(client, aluno_maior, campos):
    assert _editar(client, aluno_maior, **campos).status_code == 422


def test_cpf_invalido_do_responsavel_nao_e_devolvido(client, aluno_menor):
    resposta = _editar(client, aluno_menor, responsavel_cpf="12345678900")
    assert resposta.status_code == 422
    assert "12345678900" not in resposta.text


def test_editar_o_perfil_nao_derruba_a_sessao(client, aluno_maior):
    headers = cabecalho(aluno_maior)
    assert _editar(client, aluno_maior, telefone="21998765432").status_code == 200
    assert client.get("/v1/auth/me", headers=headers).status_code == 200

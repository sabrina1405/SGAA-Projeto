from datetime import UTC, datetime

import pytest

from tests.conftest import (
    CPF,
    CPF_RESPONSAVEL,
    TELEFONE,
    TELEFONE_RESPONSAVEL,
    cabecalho,
    nascido_ha,
)


def _listar(client, professor, **parametros):
    resposta = client.get(
        "/v1/usuarios/alunos", params=parametros, headers=cabecalho(professor)
    )
    assert resposta.status_code == 200
    return resposta.json()["dados"]


def _nomes(corpo):
    return [item["nome_completo"] for item in corpo["itens"]]


def test_listagem_exige_autenticacao(client):
    assert client.get("/v1/usuarios/alunos").status_code == 401


def test_aluno_nao_lista_alunos(client, aluno_maior):
    resposta = client.get("/v1/usuarios/alunos", headers=cabecalho(aluno_maior))
    assert resposta.status_code == 403


def test_listagem_vazia(client, professor):
    assert _listar(client, professor) == {"itens": [], "total": 0}


def test_listagem_mostra_o_telefone_do_aluno_ou_do_responsavel(
    client, professor, aluno_maior, aluno_menor
):
    corpo = _listar(client, professor)
    assert corpo["total"] == 2
    por_email = {item["email"]: item for item in corpo["itens"]}
    assert por_email["maior@exemplo.com"] == {
        "id": aluno_maior.id,
        "nome_completo": "Aluno de Teste",
        "email": "maior@exemplo.com",
        "telefone": TELEFONE,
    }
    assert por_email["menor@exemplo.com"]["telefone"] == TELEFONE_RESPONSAVEL


def test_listagem_so_tem_quem_concluiu_o_primeiro_acesso(
    client, professor, criar_usuario, aluno_maior
):
    criar_usuario("convidado@exemplo.com", senha=None)
    corpo = _listar(client, professor)
    assert corpo["total"] == 1
    assert [item["email"] for item in corpo["itens"]] == ["maior@exemplo.com"]


def test_listagem_ignora_aluno_removido(client, professor, aluno_maior, sessao):
    aluno_maior.deletado_em = datetime.now(UTC)
    sessao.commit()
    assert _listar(client, professor) == {"itens": [], "total": 0}


def test_listagem_em_ordem_alfabetica_sem_considerar_acentos(
    client, professor, criar_aluno_com_perfil
):
    for indice, nome in enumerate(["Érica Lima", "bruno Alves", "Carla Dias", "Ana"]):
        criar_aluno_com_perfil(f"a{indice}@exemplo.com", anos=15, nome_completo=nome)
    assert _nomes(_listar(client, professor)) == [
        "Ana",
        "bruno Alves",
        "Carla Dias",
        "Érica Lima",
    ]


def test_paginacao(client, professor, criar_aluno_com_perfil):
    for indice in range(5):
        criar_aluno_com_perfil(
            f"a{indice}@exemplo.com", anos=15, nome_completo=f"Aluno {indice}"
        )

    primeira = _listar(client, professor, tamanho=2)
    segunda = _listar(client, professor, tamanho=2, pagina=2)
    terceira = _listar(client, professor, tamanho=2, pagina=3)
    alem_do_fim = _listar(client, professor, tamanho=2, pagina=4)

    assert _nomes(primeira) == ["Aluno 0", "Aluno 1"]
    assert _nomes(segunda) == ["Aluno 2", "Aluno 3"]
    assert _nomes(terceira) == ["Aluno 4"]
    assert alem_do_fim == {"itens": [], "total": 5}
    assert primeira["total"] == segunda["total"] == terceira["total"] == 5


def test_nomes_iguais_mantem_ordem_estavel_entre_paginas(
    client, professor, criar_aluno_com_perfil
):
    ids = [
        criar_aluno_com_perfil(f"a{indice}@exemplo.com", anos=15).id
        for indice in range(4)
    ]
    primeira = _listar(client, professor, tamanho=2)
    segunda = _listar(client, professor, tamanho=2, pagina=2)
    assert [item["id"] for item in primeira["itens"] + segunda["itens"]] == ids


def test_tamanho_padrao_da_pagina(client, professor, criar_aluno_com_perfil):
    for indice in range(21):
        criar_aluno_com_perfil(f"a{indice}@exemplo.com", anos=15)
    corpo = _listar(client, professor)
    assert len(corpo["itens"]) == 20
    assert corpo["total"] == 21


@pytest.mark.parametrize(
    "parametros",
    [
        {"tamanho": 0},
        {"tamanho": 101},
        {"tamanho": "abc"},
        {"pagina": 0},
        {"pagina": 501},
        {"busca": "a" * 101},
        {"busca": "a\x00b"},
    ],
)
def test_parametros_invalidos_na_listagem(client, professor, parametros):
    resposta = client.get(
        "/v1/usuarios/alunos", params=parametros, headers=cabecalho(professor)
    )
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["local"][0] == "query"


@pytest.mark.parametrize(
    ("busca", "esperados"),
    [
        ("joao", ["João Pedro"]),
        ("JOÃO", ["João Pedro"]),
        ("conceicao", ["Maria Conceição"]),
        ("conceição", ["Maria Conceição"]),
        ("mari", ["Maria Conceição", "Mário Jorge"]),
        ("mario", ["Mário Jorge"]),
        ("  pedro  ", ["João Pedro"]),
        ("ceicao@", ["Maria Conceição"]),
        ("EXEMPLO.COM", ["João Pedro", "Maria Conceição", "Mário Jorge"]),
        ("ninguem", []),
    ],
)
def test_busca_por_nome_ou_email_sem_acentos_nem_maiusculas(
    client, professor, criar_aluno_com_perfil, busca, esperados
):
    criar_aluno_com_perfil("jp@exemplo.com", anos=15, nome_completo="João Pedro")
    criar_aluno_com_perfil(
        "conceicao@exemplo.com", anos=15, nome_completo="Maria Conceição"
    )
    criar_aluno_com_perfil("mj@exemplo.com", anos=15, nome_completo="Mário Jorge")

    corpo = _listar(client, professor, busca=busca)
    assert _nomes(corpo) == esperados
    assert corpo["total"] == len(esperados)


@pytest.mark.parametrize("busca", ["%", "_", "a_u", "%luno%"])
def test_curingas_do_like_sao_texto_comum(
    client, professor, criar_aluno_com_perfil, busca
):
    criar_aluno_com_perfil("a@exemplo.com", anos=15, nome_completo="Aluno Comum")
    assert _listar(client, professor, busca=busca) == {"itens": [], "total": 0}


def test_busca_encontra_curinga_literal(client, professor, criar_aluno_com_perfil):
    criar_aluno_com_perfil("a@exemplo.com", anos=15, nome_completo="Aluno 100%")
    criar_aluno_com_perfil("b@exemplo.com", anos=15, nome_completo="Aluno Comum")
    assert _nomes(_listar(client, professor, busca="100%")) == ["Aluno 100%"]


def test_busca_em_branco_nao_filtra(client, professor, aluno_maior):
    assert _listar(client, professor, busca="   ")["total"] == 1


def test_detalhe_exige_professor(client, aluno_maior):
    rota = f"/v1/usuarios/alunos/{aluno_maior.id}"
    assert client.get(rota).status_code == 401
    assert client.get(rota, headers=cabecalho(aluno_maior)).status_code == 403


def test_detalhe_de_aluno_maior_de_idade(client, professor, aluno_maior):
    resposta = client.get(
        f"/v1/usuarios/alunos/{aluno_maior.id}", headers=cabecalho(professor)
    )
    assert resposta.status_code == 200
    assert resposta.json()["dados"] == {
        "id": aluno_maior.id,
        "nome_completo": "Aluno de Teste",
        "email": "maior@exemplo.com",
        "primeiro_acesso_concluido": True,
        "perfil": {
            "data_nascimento": nascido_ha(25).isoformat(),
            "possui_responsavel": False,
            "cpf": CPF,
            "telefone": TELEFONE,
            "responsavel_nome": None,
            "responsavel_cpf": None,
            "responsavel_telefone": None,
        },
        "aulas": [],
        "pagamentos": [],
    }


def test_detalhe_de_aluno_com_responsavel(client, professor, aluno_menor):
    resposta = client.get(
        f"/v1/usuarios/alunos/{aluno_menor.id}", headers=cabecalho(professor)
    )
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


def test_detalhe_de_aluno_que_nao_concluiu_o_primeiro_acesso(
    client, professor, criar_usuario
):
    convidado = criar_usuario("convidado@exemplo.com", senha=None)
    resposta = client.get(
        f"/v1/usuarios/alunos/{convidado.id}", headers=cabecalho(professor)
    )
    assert resposta.status_code == 200
    corpo = resposta.json()["dados"]
    assert corpo["primeiro_acesso_concluido"] is False
    assert corpo["perfil"] is None


def test_detalhe_de_aluno_inexistente(client, professor, aluno_maior):
    resposta = client.get(
        f"/v1/usuarios/alunos/{aluno_maior.id + 1000}", headers=cabecalho(professor)
    )
    assert resposta.status_code == 404
    assert resposta.json() == {
        "sucesso": False,
        "mensagem": "Aluno não encontrado",
        "dados": None,
    }


def test_detalhe_de_aluno_removido(client, professor, aluno_maior, sessao):
    aluno_maior.deletado_em = datetime.now(UTC)
    sessao.commit()
    resposta = client.get(
        f"/v1/usuarios/alunos/{aluno_maior.id}", headers=cabecalho(professor)
    )
    assert resposta.status_code == 404


def test_detalhe_nao_serve_para_professor(client, professor):
    resposta = client.get(
        f"/v1/usuarios/alunos/{professor.id}", headers=cabecalho(professor)
    )
    assert resposta.status_code == 404


@pytest.mark.parametrize("aluno_id", ["0", "-1", "abc", "2147483648"])
def test_detalhe_com_id_invalido(client, professor, aluno_id):
    resposta = client.get(
        f"/v1/usuarios/alunos/{aluno_id}", headers=cabecalho(professor)
    )
    assert resposta.status_code == 422

import pytest
from sqlalchemy import select

from src.models.arquivo import Arquivo, StatusArquivo
from src.models.material import Pasta
from src.services import arquivo_service, material_service
from tests.conftest import cabecalho
from tests.test_atividades import _grupo

ROTA = "/v1/pastas"


def _criar(client, professor, nome="Apostilas", **campos):
    return client.post(
        ROTA, json={"nome": nome, **campos}, headers=cabecalho(professor)
    )


def _pasta(client, professor, nome="Apostilas", **campos):
    resposta = _criar(client, professor, nome, **campos)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()["dados"]


def _editar(client, professor, pasta_id, **campos):
    return client.patch(f"{ROTA}/{pasta_id}", json=campos, headers=cabecalho(professor))


def _detalhe(client, professor, pasta_id):
    return client.get(f"{ROTA}/{pasta_id}", headers=cabecalho(professor))


def _tipos(resposta):
    return [erro["tipo"] for erro in resposta.json()["erros"]]


@pytest.mark.parametrize(
    ("metodo", "rota", "corpo"),
    [
        ("post", ROTA, {"nome": "x"}),
        ("get", ROTA, None),
        ("get", f"{ROTA}/1", None),
        ("patch", f"{ROTA}/1", {"nome": "x"}),
        ("delete", f"{ROTA}/1", None),
        ("post", f"{ROTA}/1/arquivos", {"arquivo_ids": [1]}),
        ("patch", f"{ROTA}/1/arquivos/1", {"pasta_id": 2}),
        ("delete", f"{ROTA}/1/arquivos/1", None),
    ],
)
def test_rotas_sao_do_professor(client, aluno_maior, metodo, rota, corpo):
    sem_login = client.request(metodo, rota, json=corpo)
    assert sem_login.status_code == 401
    como_aluno = client.request(
        metodo, rota, json=corpo, headers=cabecalho(aluno_maior)
    )
    assert como_aluno.status_code == 403


# --- estrutura ---


def test_cria_raiz_e_subpastas(client, professor):
    raiz = _pasta(client, professor)
    assert raiz["pasta_pai_id"] is None
    assert raiz["raiz_id"] == raiz["id"]
    filha = _pasta(client, professor, "Módulo 1", pasta_pai_id=raiz["id"])
    neta = _pasta(client, professor, "Aula 1", pasta_pai_id=filha["id"])
    assert neta["raiz_id"] == raiz["id"]
    assert [item["nome"] for item in neta["caminho"]] == [
        "Apostilas",
        "Módulo 1",
        "Aula 1",
    ]
    detalhe = _detalhe(client, professor, raiz["id"]).json()["dados"]
    assert [item["nome"] for item in detalhe["subpastas"]] == ["Módulo 1"]
    assert detalhe["subpastas"][0]["total_subpastas"] == 1


def test_nome_repetido_no_mesmo_lugar(client, professor, outro_professor):
    raiz = _pasta(client, professor)
    assert _criar(client, professor, "apostilas").status_code == 409
    # Em outro lugar, ou de outro professor, pode.
    _pasta(client, professor, "Apostilas", pasta_pai_id=raiz["id"])
    _pasta(client, outro_professor, "Apostilas")
    # Depois de excluir, o nome fica livre.
    client.delete(f"{ROTA}/{raiz['id']}", headers=cabecalho(professor))
    _pasta(client, professor, "Apostilas")


def test_lista_raizes_e_filhas(client, professor):
    raiz = _pasta(client, professor, "B")
    _pasta(client, professor, "a")
    _pasta(client, professor, "Filha", pasta_pai_id=raiz["id"])
    raizes = client.get(ROTA, headers=cabecalho(professor)).json()["dados"]
    assert [item["nome"] for item in raizes["itens"]] == ["a", "B"]
    assert raizes["total"] == 2
    filhas = client.get(
        ROTA, params={"pasta_pai_id": raiz["id"]}, headers=cabecalho(professor)
    ).json()["dados"]
    assert [item["nome"] for item in filhas["itens"]] == ["Filha"]


def test_profundidade_maxima(client, professor, monkeypatch):
    monkeypatch.setattr(material_service, "PROFUNDIDADE_MAXIMA", 3)
    pasta = _pasta(client, professor, "1")
    for nome in ("2", "3"):
        pasta = _pasta(client, professor, nome, pasta_pai_id=pasta["id"])
    resposta = _criar(client, professor, "4", pasta_pai_id=pasta["id"])
    assert _tipos(resposta) == ["profundidade_maxima"]


def test_mover_pasta_recalcula_a_raiz(client, professor, sessao):
    origem = _pasta(client, professor, "Origem")
    filha = _pasta(client, professor, "Filha", pasta_pai_id=origem["id"])
    neta = _pasta(client, professor, "Neta", pasta_pai_id=filha["id"])
    destino = _pasta(client, professor, "Destino")

    resposta = _editar(client, professor, filha["id"], pasta_pai_id=destino["id"])
    assert resposta.status_code == 200
    sessao.expire_all()
    assert sessao.get(Pasta, filha["id"]).raiz_id == destino["id"]
    assert sessao.get(Pasta, neta["id"]).raiz_id == destino["id"]

    # Para a raiz: vira a própria raiz da subárvore.
    _editar(client, professor, filha["id"], pasta_pai_id=None)
    sessao.expire_all()
    assert sessao.get(Pasta, neta["id"]).raiz_id == filha["id"]


def test_mover_para_dentro_dela_mesma(client, professor):
    raiz = _pasta(client, professor)
    filha = _pasta(client, professor, "Filha", pasta_pai_id=raiz["id"])
    for destino in (raiz["id"], filha["id"]):
        resposta = _editar(client, professor, raiz["id"], pasta_pai_id=destino)
        assert _tipos(resposta) == ["ciclo"]


def test_mover_respeita_a_profundidade(client, professor, monkeypatch):
    monkeypatch.setattr(material_service, "PROFUNDIDADE_MAXIMA", 3)
    funda = _pasta(client, professor, "A")
    funda = _pasta(client, professor, "B", pasta_pai_id=funda["id"])
    galho = _pasta(client, professor, "Galho")
    _pasta(client, professor, "Folha", pasta_pai_id=galho["id"])
    resposta = _editar(client, professor, galho["id"], pasta_pai_id=funda["id"])
    assert _tipos(resposta) == ["profundidade_maxima"]


def test_mover_com_nome_repetido_no_destino(client, professor):
    destino = _pasta(client, professor, "Destino")
    _pasta(client, professor, "Igual", pasta_pai_id=destino["id"])
    outra = _pasta(client, professor, "Igual")
    assert (
        _editar(client, professor, outra["id"], pasta_pai_id=destino["id"]).status_code
        == 409
    )


def test_editar_nome(client, professor):
    pasta = _pasta(client, professor)
    resposta = _editar(client, professor, pasta["id"], nome="  Listas   de exercícios ")
    assert resposta.json()["dados"]["nome"] == "Listas de exercícios"
    assert _editar(client, professor, pasta["id"]).status_code == 422
    assert _editar(client, professor, pasta["id"], nome=None).status_code == 422


# --- destinatários ---


def test_destinatarios_na_raiz(client, professor, aluno_maior):
    grupo_id = _grupo(client, professor, [aluno_maior.id])
    pasta = _pasta(client, professor, aluno_ids=[aluno_maior.id], grupo_ids=[grupo_id])
    assert [aluno["id"] for aluno in pasta["alunos"]] == [aluno_maior.id]
    assert [grupo["id"] for grupo in pasta["grupos"]] == [grupo_id]
    filha = _pasta(client, professor, "Filha", pasta_pai_id=pasta["id"])
    # A subpasta mostra os destinatários herdados da raiz.
    assert [aluno["id"] for aluno in filha["alunos"]] == [aluno_maior.id]


def test_destinatarios_so_na_raiz(client, professor, aluno_maior):
    raiz = _pasta(client, professor)
    resposta = _criar(
        client, professor, "Filha", pasta_pai_id=raiz["id"], todos_alunos=True
    )
    assert _tipos(resposta) == ["destinatarios_so_na_raiz"]
    filha = _pasta(client, professor, "Filha", pasta_pai_id=raiz["id"])
    resposta = _editar(client, professor, filha["id"], aluno_ids=[aluno_maior.id])
    assert _tipos(resposta) == ["destinatarios_so_na_raiz"]


def test_destinatarios_conflitantes(client, professor, aluno_maior):
    resposta = _criar(client, professor, todos_alunos=True, aluno_ids=[aluno_maior.id])
    assert _tipos(resposta) == ["destinatarios_conflitantes"]


def test_raiz_que_vira_subpasta_perde_os_destinatarios(client, professor, aluno_maior):
    raiz = _pasta(client, professor, "Antiga", aluno_ids=[aluno_maior.id])
    nova = _pasta(client, professor, "Nova", todos_grupos=True)
    movida = _editar(client, professor, raiz["id"], pasta_pai_id=nova["id"]).json()[
        "dados"
    ]
    assert movida["alunos"] == []
    assert movida["todos_grupos"] is True
    # De volta à raiz, começa sem destinatários.
    devolvida = _editar(client, professor, raiz["id"], pasta_pai_id=None).json()[
        "dados"
    ]
    assert devolvida["todos_grupos"] is False
    assert devolvida["alunos"] == []


def test_trocar_destinatarios(client, professor, aluno_maior, criar_aluno_com_perfil):
    outro = criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")
    pasta = _pasta(client, professor, aluno_ids=[aluno_maior.id])
    resposta = _editar(client, professor, pasta["id"], aluno_ids=[outro.id])
    assert [aluno["id"] for aluno in resposta.json()["dados"]["alunos"]] == [outro.id]


# --- materiais ---


def test_adicionar_mover_e_remover_material(
    client, professor, arquivo_confirmado, sessao
):
    pasta = _pasta(client, professor)
    outra = _pasta(client, professor, "Outra")
    arquivo_id = arquivo_confirmado(professor, "apostila.pdf")
    resposta = client.post(
        f"{ROTA}/{pasta['id']}/arquivos",
        json={"arquivo_ids": [arquivo_id]},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 200
    assert [item["nome"] for item in resposta.json()["dados"]["arquivos"]] == [
        "apostila.pdf"
    ]

    resposta = client.patch(
        f"{ROTA}/{pasta['id']}/arquivos/{arquivo_id}",
        json={"pasta_id": outra["id"]},
        headers=cabecalho(professor),
    )
    assert resposta.json()["dados"]["id"] == outra["id"]
    assert _detalhe(client, professor, pasta["id"]).json()["dados"]["arquivos"] == []

    rota = f"{ROTA}/{outra['id']}/arquivos/{arquivo_id}"
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 200
    assert sessao.get(Arquivo, arquivo_id).status == StatusArquivo.REMOVER
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 404


def test_material_invalido(client, professor, outro_professor, arquivo_confirmado):
    pasta = _pasta(client, professor)
    de_outro = arquivo_confirmado(outro_professor)
    resposta = client.post(
        f"{ROTA}/{pasta['id']}/arquivos",
        json={"arquivo_ids": [de_outro]},
        headers=cabecalho(professor),
    )
    assert _tipos(resposta) == ["arquivo_invalido"]
    # Um arquivo só fica em um lugar.
    meu = arquivo_confirmado(professor)
    corpo = {"arquivo_ids": [meu]}
    rota = f"{ROTA}/{pasta['id']}/arquivos"
    assert (
        client.post(rota, json=corpo, headers=cabecalho(professor)).status_code == 200
    )
    resposta = client.post(rota, json=corpo, headers=cabecalho(professor))
    assert _tipos(resposta) == ["arquivo_invalido"]


def test_material_na_pasta_nao_e_apagado_pela_limpeza(
    client, professor, arquivo_confirmado, drive, sessao, monkeypatch
):
    pasta = _pasta(client, professor)
    arquivo_id = arquivo_confirmado(professor)
    client.post(
        f"{ROTA}/{pasta['id']}/arquivos",
        json={"arquivo_ids": [arquivo_id]},
        headers=cabecalho(professor),
    )
    from datetime import timedelta

    from src.core.security import agora

    momento = agora() + timedelta(days=2)
    monkeypatch.setattr(arquivo_service, "agora", lambda: momento)
    assert arquivo_service.limpar(sessao, drive) == 0
    assert sessao.get(Arquivo, arquivo_id).deletado_em is None


def test_excluir_apaga_a_subarvore_e_os_materiais(
    client, professor, arquivo_confirmado, sessao
):
    raiz = _pasta(client, professor)
    filha = _pasta(client, professor, "Filha", pasta_pai_id=raiz["id"])
    neta = _pasta(client, professor, "Neta", pasta_pai_id=filha["id"])
    arquivo_id = arquivo_confirmado(professor)
    client.post(
        f"{ROTA}/{neta['id']}/arquivos",
        json={"arquivo_ids": [arquivo_id]},
        headers=cabecalho(professor),
    )
    assert (
        client.delete(f"{ROTA}/{raiz['id']}", headers=cabecalho(professor)).status_code
        == 200
    )
    sessao.expire_all()
    ativas = sessao.scalars(select(Pasta.id).where(Pasta.deletado_em.is_(None))).all()
    assert ativas == []
    assert sessao.get(Arquivo, arquivo_id).status == StatusArquivo.REMOVER
    assert _detalhe(client, professor, neta["id"]).status_code == 404


# --- outro professor ---


def test_professor_nao_mexe_nas_pastas_de_outro(
    client, professor, outro_professor, arquivo_confirmado
):
    pasta = _pasta(client, professor)
    arquivo_id = arquivo_confirmado(professor)
    client.post(
        f"{ROTA}/{pasta['id']}/arquivos",
        json={"arquivo_ids": [arquivo_id]},
        headers=cabecalho(professor),
    )
    dele = cabecalho(outro_professor)
    rota = f"{ROTA}/{pasta['id']}"
    assert client.get(rota, headers=dele).status_code == 404
    assert client.patch(rota, json={"nome": "x"}, headers=dele).status_code == 404
    assert client.delete(rota, headers=dele).status_code == 404
    assert (
        client.get(ROTA, params={"pasta_pai_id": pasta["id"]}, headers=dele).status_code
        == 404
    )
    meu_arquivo = arquivo_confirmado(outro_professor)
    assert (
        client.post(
            f"{rota}/arquivos", json={"arquivo_ids": [meu_arquivo]}, headers=dele
        ).status_code
        == 404
    )
    assert (
        client.delete(f"{rota}/arquivos/{arquivo_id}", headers=dele).status_code == 404
    )

    # Usar a pasta do outro como destino é um campo inválido.
    minha = _pasta(client, outro_professor)
    resposta = _criar(client, outro_professor, "Filha", pasta_pai_id=pasta["id"])
    assert _tipos(resposta) == ["pasta_invalida"]
    resposta = _editar(client, outro_professor, minha["id"], pasta_pai_id=pasta["id"])
    assert _tipos(resposta) == ["pasta_invalida"]
    # Nada mudou na pasta do professor.
    detalhe = _detalhe(client, professor, pasta["id"]).json()["dados"]
    assert detalhe["subpastas"] == []
    assert [item["id"] for item in detalhe["arquivos"]] == [arquivo_id]


def test_grupo_de_outro_professor(client, professor, outro_professor):
    grupo_id = _grupo(client, outro_professor)
    resposta = _criar(client, professor, grupo_ids=[grupo_id])
    assert _tipos(resposta) == ["grupo_invalido"]


def test_mover_material_invalido(
    client, professor, outro_professor, arquivo_confirmado
):
    pasta = _pasta(client, professor)
    outra = _pasta(client, professor, "Outra")
    arquivo_id = arquivo_confirmado(professor)
    client.post(
        f"{ROTA}/{pasta['id']}/arquivos",
        json={"arquivo_ids": [arquivo_id]},
        headers=cabecalho(professor),
    )
    # Não está nesta pasta.
    resposta = client.patch(
        f"{ROTA}/{outra['id']}/arquivos/{arquivo_id}",
        json={"pasta_id": pasta["id"]},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 404
    # Destino de outro professor.
    dele = _pasta(client, outro_professor)
    resposta = client.patch(
        f"{ROTA}/{pasta['id']}/arquivos/{arquivo_id}",
        json={"pasta_id": dele["id"]},
        headers=cabecalho(professor),
    )
    assert _tipos(resposta) == ["pasta_invalida"]

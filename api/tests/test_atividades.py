from datetime import timedelta

import pytest
from sqlalchemy import select

from src.core.security import agora
from src.models.arquivo import Arquivo, StatusArquivo
from src.services import arquivo_service, atividade_service
from tests.conftest import cabecalho

ROTA = "/v1/atividades"
ROTA_ALUNO = "/v1/minhas-atividades"
BRASILIA = "-03:00"


def _quando(**tempo):
    return (agora() + timedelta(**tempo)).isoformat()


def _corpo(**campos):
    return {
        "titulo": "Redação",
        "descricao": "Escreva **30 linhas**.",
        "liberar_em": _quando(hours=-1),
        "vence_em": _quando(days=10),
        "todos_alunos": True,
        **campos,
    }


def _criar(client, professor, **campos):
    return client.post(ROTA, json=_corpo(**campos), headers=cabecalho(professor))


def _atividade(client, professor, **campos):
    resposta = _criar(client, professor, **campos)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()["dados"]


def _editar(client, professor, atividade_id, **campos):
    return client.patch(
        f"{ROTA}/{atividade_id}", json=campos, headers=cabecalho(professor)
    )


def _listar(client, professor, rota=ROTA, **parametros):
    resposta = client.get(rota, params=parametros, headers=cabecalho(professor))
    assert resposta.status_code == 200, resposta.json()
    return resposta.json()["dados"]


def _grupo(client, professor, aluno_ids=()):
    resposta = client.post(
        "/v1/grupos",
        json={"titulo": "Turma A", "aluno_ids": list(aluno_ids)},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 201
    return resposta.json()["dados"]["id"]


def _entregar(client, aluno, atividade_id, **campos):
    return client.put(
        f"{ROTA_ALUNO}/{atividade_id}/entrega",
        json={"resposta": "Minha resposta", **campos},
        headers=cabecalho(aluno),
    )


def _tipos_de_erro(resposta):
    assert resposta.status_code == 422, resposta.json()
    return [(erro["local"], erro["tipo"]) for erro in resposta.json()["erros"]]


def _status_do_arquivo(sessao, arquivo_id):
    sessao.expire_all()
    return sessao.get(Arquivo, arquivo_id).status


@pytest.fixture
def outro_aluno(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")


@pytest.mark.parametrize(
    ("metodo", "rota", "corpo"),
    [
        ("post", ROTA, {"titulo": "X"}),
        ("get", ROTA, None),
        ("get", f"{ROTA}/entregas", None),
        ("get", f"{ROTA}/1", None),
        ("patch", f"{ROTA}/1", {"titulo": "X"}),
        ("delete", f"{ROTA}/1", None),
        ("get", f"{ROTA}/1/entregas/2", None),
    ],
)
def test_atividades_exigem_professor(client, aluno_maior, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401
    resposta = client.request(metodo, rota, json=corpo, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 403


# --- criação ---


def test_cria_atividade(client, professor, aluno_maior, arquivo_confirmado):
    arquivo_id = arquivo_confirmado(professor)
    grupo_id = _grupo(client, professor)
    dados = _atividade(
        client,
        professor,
        todos_alunos=False,
        aluno_ids=[aluno_maior.id],
        grupo_ids=[grupo_id],
        arquivo_ids=[arquivo_id],
        permite_envio_arquivo=True,
    )
    assert dados["titulo"] == "Redação"
    assert dados["descricao"] == "Escreva **30 linhas**."
    assert dados["permite_envio_arquivo"] is True
    assert dados["vence_em"].endswith(BRASILIA)
    assert [aluno["id"] for aluno in dados["alunos"]] == [aluno_maior.id]
    assert [grupo["id"] for grupo in dados["grupos"]] == [grupo_id]
    assert [anexo["id"] for anexo in dados["anexos"]] == [arquivo_id]
    assert dados["anexos"][0]["url"].startswith("https://drive.exemplo/ver/")


@pytest.mark.parametrize("campo", ["titulo", "descricao", "liberar_em", "vence_em"])
def test_campos_obrigatorios(client, professor, campo):
    corpo = _corpo()
    del corpo[campo]
    resposta = client.post(ROTA, json=corpo, headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_data_sem_fuso_e_recusada(client, professor):
    resposta = _criar(client, professor, vence_em="2030-01-10T15:00:00")
    assert (["body", "vence_em"], "timezone_aware") in _tipos_de_erro(resposta)


def test_periodo_invalido(client, professor):
    resposta = _criar(
        client, professor, liberar_em=_quando(days=5), vence_em=_quando(days=4)
    )
    assert _tipos_de_erro(resposta) == [(["body", "vence_em"], "periodo_invalido")]
    resposta = _criar(
        client, professor, liberar_em=_quando(days=-5), vence_em=_quando(days=-1)
    )
    assert _tipos_de_erro(resposta) == [(["body", "vence_em"], "periodo_invalido")]


def test_destinatarios(client, professor, outro_professor, aluno, aluno_maior):
    resposta = _criar(client, professor, todos_alunos=False)
    assert (["body", "aluno_ids"], "sem_destinatario") in _tipos_de_erro(resposta)
    resposta = _criar(client, professor, aluno_ids=[aluno_maior.id])
    assert _tipos_de_erro(resposta) == [
        (["body", "aluno_ids"], "destinatarios_conflitantes")
    ]
    resposta = _criar(client, professor, todos_alunos=False, aluno_ids=[aluno.id])
    assert _tipos_de_erro(resposta) == [(["body", "aluno_ids"], "aluno_invalido")]
    alheio = _grupo(client, outro_professor)
    resposta = _criar(client, professor, todos_alunos=False, grupo_ids=[alheio])
    assert _tipos_de_erro(resposta) == [(["body", "grupo_ids"], "grupo_invalido")]


def test_arquivo_invalido_nao_cria_nada(
    client, professor, outro_professor, arquivo_confirmado, drive
):
    alheio = arquivo_confirmado(outro_professor)
    pendente = client.post(
        "/v1/arquivos/sessao",
        json={"nome": "a.pdf", "tipo_mime": "application/pdf", "tamanho": 1},
        headers=cabecalho(professor),
    ).json()["dados"]["arquivo_id"]
    for arquivo_id in (alheio, pendente, 999999):
        resposta = _criar(client, professor, arquivo_ids=[arquivo_id])
        assert _tipos_de_erro(resposta) == [
            (["body", "arquivo_ids"], "arquivo_invalido")
        ]
    assert _listar(client, professor)["total"] == 0


def test_arquivo_nao_serve_para_duas_atividades(client, professor, arquivo_confirmado):
    arquivo_id = arquivo_confirmado(professor)
    _atividade(client, professor, arquivo_ids=[arquivo_id])
    resposta = _criar(client, professor, arquivo_ids=[arquivo_id])
    assert _tipos_de_erro(resposta) == [(["body", "arquivo_ids"], "arquivo_invalido")]


def test_limite_de_anexos(client, professor):
    resposta = _criar(client, professor, arquivo_ids=[1, 2, 3, 4, 5, 6])
    assert resposta.status_code == 422


# --- listagem e detalhe ---


def test_lista_por_situacao(client, professor, outro_professor, monkeypatch):
    perto = _atividade(client, professor, vence_em=_quando(days=1))
    longe = _atividade(client, professor, vence_em=_quando(days=9))
    _atividade(client, outro_professor)

    dados = _listar(client, professor)
    assert dados["total"] == 2
    assert [item["id"] for item in dados["itens"]] == [perto["id"], longe["id"]]
    assert dados["itens"][0]["total_entregas"] == 0

    momento = agora() + timedelta(days=2)
    monkeypatch.setattr(atividade_service, "agora", lambda: momento)
    assert [
        item["id"] for item in _listar(client, professor, situacao="vencidas")["itens"]
    ] == [perto["id"]]
    assert [
        item["id"] for item in _listar(client, professor, situacao="proximas")["itens"]
    ] == [longe["id"]]


def test_situacao_desconhecida(client, professor):
    resposta = client.get(ROTA, params={"situacao": "x"}, headers=cabecalho(professor))
    assert resposta.status_code == 422


def test_atividade_de_outro_professor(client, professor, outro_professor, aluno_maior):
    atividade = _atividade(client, outro_professor)
    rota = f"{ROTA}/{atividade['id']}"
    cab = cabecalho(professor)
    assert client.get(rota, headers=cab).status_code == 404
    assert _editar(client, professor, atividade["id"], titulo="X").status_code == 404
    assert client.delete(rota, headers=cab).status_code == 404
    _entregar(client, aluno_maior, atividade["id"])
    resposta = client.get(f"{rota}/entregas/{aluno_maior.id}", headers=cab)
    assert resposta.status_code == 404


# --- edição ---


def test_edita_so_o_enviado(client, professor):
    atividade = _atividade(client, professor)
    resposta = _editar(client, professor, atividade["id"], titulo="Conto")
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["titulo"] == "Conto"
    assert dados["descricao"] == atividade["descricao"]


@pytest.mark.parametrize("corpo", [{}, {"titulo": None}, {"vence_em": None}])
def test_edicao_invalida(client, professor, corpo):
    atividade = _atividade(client, professor)
    assert _editar(client, professor, atividade["id"], **corpo).status_code == 422


def test_periodo_conferido_com_o_que_esta_salvo(client, professor):
    atividade = _atividade(client, professor, liberar_em=_quando(days=2))
    resposta = _editar(client, professor, atividade["id"], vence_em=_quando(days=1))
    assert _tipos_de_erro(resposta) == [(["body", "vence_em"], "periodo_invalido")]


def test_nao_exige_vencimento_futuro_se_a_data_nao_mudou(
    client, professor, monkeypatch
):
    atividade = _atividade(client, professor)
    momento = agora() + timedelta(days=30)
    monkeypatch.setattr(atividade_service, "agora", lambda: momento)
    resposta = _editar(client, professor, atividade["id"], titulo="Conto")
    assert resposta.status_code == 200


def test_troca_os_destinatarios(client, professor, aluno_maior, outro_aluno):
    atividade = _atividade(
        client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id]
    )
    resposta = _editar(client, professor, atividade["id"], aluno_ids=[outro_aluno.id])
    assert [aluno["id"] for aluno in resposta.json()["dados"]["alunos"]] == [
        outro_aluno.id
    ]
    resposta = _editar(client, professor, atividade["id"], aluno_ids=[])
    assert (["body", "aluno_ids"], "sem_destinatario") in _tipos_de_erro(resposta)


def test_substituir_anexos_marca_o_que_saiu(
    client, professor, arquivo_confirmado, sessao
):
    primeiro = arquivo_confirmado(professor)
    segundo = arquivo_confirmado(professor)
    atividade = _atividade(client, professor, arquivo_ids=[primeiro])
    resposta = _editar(
        client, professor, atividade["id"], arquivo_ids=[primeiro, segundo]
    )
    assert [a["id"] for a in resposta.json()["dados"]["anexos"]] == [primeiro, segundo]
    assert _status_do_arquivo(sessao, primeiro) == StatusArquivo.CONFIRMADO

    resposta = _editar(client, professor, atividade["id"], arquivo_ids=[segundo])
    assert [a["id"] for a in resposta.json()["dados"]["anexos"]] == [segundo]
    assert _status_do_arquivo(sessao, primeiro) == StatusArquivo.REMOVER
    assert _status_do_arquivo(sessao, segundo) == StatusArquivo.CONFIRMADO


# --- exclusão ---


def test_excluir_marca_os_arquivos_e_some_das_listas(
    client, professor, aluno_maior, arquivo_confirmado, drive, sessao
):
    do_professor = arquivo_confirmado(professor)
    do_aluno = arquivo_confirmado(aluno_maior)
    atividade = _atividade(
        client,
        professor,
        arquivo_ids=[do_professor],
        permite_envio_arquivo=True,
    )
    assert (
        _entregar(
            client, aluno_maior, atividade["id"], arquivo_ids=[do_aluno]
        ).status_code
        == 200
    )
    rota = f"{ROTA}/{atividade['id']}"
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 200

    assert _status_do_arquivo(sessao, do_professor) == StatusArquivo.REMOVER
    assert _status_do_arquivo(sessao, do_aluno) == StatusArquivo.REMOVER
    assert client.get(rota, headers=cabecalho(professor)).status_code == 404
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 404
    assert _listar(client, professor)["total"] == 0
    assert _listar(client, aluno_maior, ROTA_ALUNO)["total"] == 0
    assert _listar(client, professor, f"{ROTA}/entregas")["total"] == 0

    assert arquivo_service.limpar(sessao, drive) == 2
    assert sorted(drive.apagados) == sorted(
        [f"drive-{do_professor}", f"drive-{do_aluno}"]
    )


# --- acompanhamento ---


def test_acompanhamento_por_aluno(
    client, professor, aluno_maior, outro_aluno, monkeypatch
):
    perto = _atividade(client, professor, vence_em=_quando(days=1))
    longe = _atividade(client, professor, vence_em=_quando(days=9))
    assert _entregar(client, aluno_maior, longe["id"]).status_code == 200

    dados = _listar(client, professor, f"{ROTA}/entregas")
    assert dados["total"] == 4
    primeiro = dados["itens"][0]
    assert primeiro["atividade_id"] == perto["id"]
    assert primeiro["aluno_nome"] == "Aluno de Teste"
    assert primeiro["status"] is None
    assert primeiro["enviada_em"] is None

    entregues = _listar(client, professor, f"{ROTA}/entregas", situacao="entregues")
    assert [
        (item["atividade_id"], item["aluno_id"], item["status"])
        for item in entregues["itens"]
    ] == [(longe["id"], aluno_maior.id, "enviado")]
    assert (
        _listar(client, professor, f"{ROTA}/entregas", situacao="proximas")["total"]
        == 3
    )
    assert (
        _listar(client, professor, f"{ROTA}/entregas", situacao="vencidas")["total"]
        == 0
    )

    momento = agora() + timedelta(days=2)
    monkeypatch.setattr(atividade_service, "agora", lambda: momento)
    vencidas = _listar(client, professor, f"{ROTA}/entregas", situacao="vencidas")
    assert {item["atividade_id"] for item in vencidas["itens"]} == {perto["id"]}
    assert vencidas["total"] == 2


def test_entrega_continua_apos_sair_dos_destinatarios(
    client, professor, aluno_maior, outro_aluno
):
    atividade = _atividade(
        client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id]
    )
    _entregar(client, aluno_maior, atividade["id"])
    _editar(client, professor, atividade["id"], aluno_ids=[outro_aluno.id])
    entregues = _listar(client, professor, f"{ROTA}/entregas", situacao="entregues")
    assert [item["aluno_id"] for item in entregues["itens"]] == [aluno_maior.id]


def test_detalhe_da_entrega(client, professor, aluno_maior, arquivo_confirmado):
    arquivo_id = arquivo_confirmado(aluno_maior)
    atividade = _atividade(client, professor, permite_envio_arquivo=True)
    rota = f"{ROTA}/{atividade['id']}/entregas/{aluno_maior.id}"
    assert client.get(rota, headers=cabecalho(professor)).status_code == 404

    _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[arquivo_id])
    resposta = client.get(rota, headers=cabecalho(professor))
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["resposta"] == "Minha resposta"
    assert [anexo["id"] for anexo in dados["anexos"]] == [arquivo_id]


def test_arquivos_ficam_fora_da_limpeza_se_vinculados(
    client, professor, arquivo_confirmado, drive, sessao, monkeypatch
):
    arquivo_id = arquivo_confirmado(professor)
    _atividade(client, professor, arquivo_ids=[arquivo_id])
    momento = agora() + timedelta(days=3)
    monkeypatch.setattr(arquivo_service, "agora", lambda: momento)
    assert arquivo_service.limpar(sessao, drive) == 0
    assert (
        sessao.scalar(select(Arquivo.deletado_em).where(Arquivo.id == arquivo_id))
        is None
    )

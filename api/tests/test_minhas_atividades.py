from datetime import timedelta

import pytest

from src.core.security import agora
from src.models.arquivo import Arquivo, StatusArquivo
from src.services import atividade_service
from tests.conftest import cabecalho
from tests.test_atividades import _atividade, _editar, _entregar, _grupo, _quando

ROTA = "/v1/minhas-atividades"


def _listar(client, aluno, **parametros):
    resposta = client.get(ROTA, params=parametros, headers=cabecalho(aluno))
    assert resposta.status_code == 200, resposta.json()
    return resposta.json()["dados"]


def _ids(dados):
    return [item["id"] for item in dados["itens"]]


def _detalhe(client, aluno, atividade_id):
    return client.get(f"{ROTA}/{atividade_id}", headers=cabecalho(aluno))


def _ir_para(monkeypatch, **tempo):
    momento = agora() + timedelta(**tempo)
    monkeypatch.setattr(atividade_service, "agora", lambda: momento)


@pytest.fixture
def outro_aluno(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")


@pytest.mark.parametrize(
    ("metodo", "rota", "corpo"),
    [
        ("get", ROTA, None),
        ("get", f"{ROTA}/1", None),
        ("put", f"{ROTA}/1/entrega", {"resposta": "x"}),
    ],
)
def test_exigem_aluno(client, professor, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401
    resposta = client.request(metodo, rota, json=corpo, headers=cabecalho(professor))
    assert resposta.status_code == 403


# --- visibilidade ---


def test_aluno_escolhido(client, professor, aluno_maior, outro_aluno):
    atividade = _atividade(
        client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id]
    )
    assert _ids(_listar(client, aluno_maior)) == [atividade["id"]]
    assert _ids(_listar(client, outro_aluno)) == []
    assert _detalhe(client, outro_aluno, atividade["id"]).status_code == 404
    assert _entregar(client, outro_aluno, atividade["id"]).status_code == 404


def test_todos_os_alunos(client, professor, aluno_maior, outro_aluno):
    atividade = _atividade(client, professor)
    assert _ids(_listar(client, outro_aluno)) == [atividade["id"]]


def test_por_grupo_e_dinamico(client, professor, aluno_maior, outro_aluno):
    grupo_id = _grupo(client, professor, [aluno_maior.id])
    atividade = _atividade(client, professor, todos_alunos=False, grupo_ids=[grupo_id])
    assert _ids(_listar(client, aluno_maior)) == [atividade["id"]]
    assert _ids(_listar(client, outro_aluno)) == []

    client.post(
        f"/v1/grupos/{grupo_id}/alunos",
        json={"aluno_ids": [outro_aluno.id]},
        headers=cabecalho(professor),
    )
    assert _ids(_listar(client, outro_aluno)) == [atividade["id"]]


def test_todos_os_grupos_so_do_professor(
    client, professor, outro_professor, aluno_maior, outro_aluno
):
    _grupo(client, professor, [aluno_maior.id])
    _grupo(client, outro_professor, [outro_aluno.id])
    atividade = _atividade(client, professor, todos_alunos=False, todos_grupos=True)
    assert _ids(_listar(client, aluno_maior)) == [atividade["id"]]
    assert _ids(_listar(client, outro_aluno)) == []


def test_antes_da_liberacao_nao_aparece(client, professor, aluno_maior, monkeypatch):
    atividade = _atividade(client, professor, liberar_em=_quando(days=2))
    assert _ids(_listar(client, aluno_maior)) == []
    assert _detalhe(client, aluno_maior, atividade["id"]).status_code == 404
    assert _entregar(client, aluno_maior, atividade["id"]).status_code == 404

    _ir_para(monkeypatch, days=3)
    assert _ids(_listar(client, aluno_maior)) == [atividade["id"]]
    assert _detalhe(client, aluno_maior, atividade["id"]).status_code == 200


def test_detalhe(client, professor, aluno_maior, arquivo_confirmado):
    arquivo_id = arquivo_confirmado(professor)
    atividade = _atividade(client, professor, arquivo_ids=[arquivo_id])
    resposta = _detalhe(client, aluno_maior, atividade["id"])
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["titulo"] == "Redação"
    assert dados["professor_nome"] == "Usuário de Teste"
    assert [anexo["id"] for anexo in dados["anexos"]] == [arquivo_id]
    assert dados["entrega"] is None


def test_situacoes(client, professor, aluno_maior, monkeypatch):
    vence_logo = _atividade(client, professor, vence_em=_quando(days=1))
    entregue = _atividade(client, professor, vence_em=_quando(days=3))
    aberta = _atividade(client, professor, vence_em=_quando(days=9))
    _entregar(client, aluno_maior, entregue["id"])

    _ir_para(monkeypatch, days=2)
    assert _ids(_listar(client, aluno_maior, situacao="vencidas")) == [vence_logo["id"]]
    assert _ids(_listar(client, aluno_maior, situacao="proximas")) == [aberta["id"]]
    realizadas = _listar(client, aluno_maior, situacao="realizadas")
    assert _ids(realizadas) == [entregue["id"]]
    assert realizadas["itens"][0]["status"] == "enviado"
    assert _listar(client, aluno_maior)["total"] == 3


def test_paginacao(client, professor, aluno_maior):
    _atividade(client, professor, vence_em=_quando(days=1))
    segunda = _atividade(client, professor, vence_em=_quando(days=2))
    dados = _listar(client, aluno_maior, pagina=2, tamanho=1)
    assert dados["total"] == 2
    assert _ids(dados) == [segunda["id"]]


# --- entrega ---


def test_entrega_no_prazo(client, professor, aluno_maior):
    atividade = _atividade(client, professor)
    resposta = _entregar(client, aluno_maior, atividade["id"])
    assert resposta.status_code == 200
    dados = resposta.json()["dados"]
    assert dados["resposta"] == "Minha resposta"
    assert dados["status"] == "enviado"
    assert dados["enviada_em"].endswith("-03:00")
    detalhe = _detalhe(client, aluno_maior, atividade["id"]).json()["dados"]
    assert detalhe["entrega"]["resposta"] == "Minha resposta"


@pytest.mark.parametrize("resposta", ["", "   "])
def test_resposta_obrigatoria(client, professor, aluno_maior, resposta):
    atividade = _atividade(client, professor)
    assert (
        _entregar(client, aluno_maior, atividade["id"], resposta=resposta).status_code
        == 422
    )


def test_sem_o_campo_resposta(client, professor, aluno_maior):
    atividade = _atividade(client, professor)
    resposta = client.put(
        f"{ROTA}/{atividade['id']}/entrega", json={}, headers=cabecalho(aluno_maior)
    )
    assert resposta.status_code == 422


def test_edita_ate_o_vencimento(client, professor, aluno_maior, monkeypatch):
    atividade = _atividade(client, professor, vence_em=_quando(days=1))
    _entregar(client, aluno_maior, atividade["id"])
    resposta = _entregar(client, aluno_maior, atividade["id"], resposta="Corrigida")
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["resposta"] == "Corrigida"
    assert resposta.json()["dados"]["status"] == "enviado"

    _ir_para(monkeypatch, days=2)
    resposta = _entregar(client, aluno_maior, atividade["id"], resposta="Tarde demais")
    assert resposta.status_code == 409
    detalhe = _detalhe(client, aluno_maior, atividade["id"]).json()["dados"]
    assert detalhe["entrega"]["resposta"] == "Corrigida"


def test_entrega_atrasada(client, professor, aluno_maior, monkeypatch):
    atividade = _atividade(client, professor, vence_em=_quando(days=1))
    _ir_para(monkeypatch, days=2)
    resposta = _entregar(client, aluno_maior, atividade["id"])
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["status"] == "entregue_com_atraso"
    # Depois de entregar com atraso, não edita.
    assert _entregar(client, aluno_maior, atividade["id"]).status_code == 409


def test_entrega_atrasada_com_arquivo_em_uma_chamada(
    client, professor, aluno_maior, arquivo_confirmado, monkeypatch
):
    arquivo_id = arquivo_confirmado(aluno_maior)
    atividade = _atividade(
        client, professor, vence_em=_quando(days=1), permite_envio_arquivo=True
    )
    _ir_para(monkeypatch, days=2)
    resposta = _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[arquivo_id])
    assert resposta.status_code == 200
    assert [anexo["id"] for anexo in resposta.json()["dados"]["anexos"]] == [arquivo_id]


def test_entrega_com_arquivo_desligado(
    client, professor, aluno_maior, arquivo_confirmado
):
    arquivo_id = arquivo_confirmado(aluno_maior)
    atividade = _atividade(client, professor)
    resposta = _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[arquivo_id])
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["tipo"] == "envio_de_arquivo_desligado"


def test_arquivo_de_outro_aluno(
    client, professor, aluno_maior, outro_aluno, arquivo_confirmado
):
    alheio = arquivo_confirmado(outro_aluno)
    atividade = _atividade(client, professor, permite_envio_arquivo=True)
    resposta = _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[alheio])
    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["tipo"] == "arquivo_invalido"
    detalhe = _detalhe(client, aluno_maior, atividade["id"]).json()["dados"]
    assert detalhe["entrega"] is None


def test_limite_de_arquivos_na_entrega(client, professor, aluno_maior):
    atividade = _atividade(client, professor, permite_envio_arquivo=True)
    resposta = _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[1, 2, 3, 4])
    assert resposta.status_code == 422


def test_substituir_arquivos_da_entrega(
    client, professor, aluno_maior, arquivo_confirmado, sessao
):
    primeiro = arquivo_confirmado(aluno_maior)
    segundo = arquivo_confirmado(aluno_maior)
    atividade = _atividade(client, professor, permite_envio_arquivo=True)
    _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[primeiro])

    # Sem `arquivo_ids`, mantém.
    resposta = _entregar(client, aluno_maior, atividade["id"], resposta="Outra")
    assert [a["id"] for a in resposta.json()["dados"]["anexos"]] == [primeiro]

    resposta = _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[segundo])
    assert [a["id"] for a in resposta.json()["dados"]["anexos"]] == [segundo]
    sessao.expire_all()
    assert sessao.get(Arquivo, primeiro).status == StatusArquivo.REMOVER

    resposta = _entregar(client, aluno_maior, atividade["id"], arquivo_ids=[])
    assert resposta.json()["dados"]["anexos"] == []
    sessao.expire_all()
    assert sessao.get(Arquivo, segundo).status == StatusArquivo.REMOVER


def test_quem_saiu_dos_destinatarios_ve_a_propria_entrega(
    client, professor, aluno_maior, outro_aluno
):
    atividade = _atividade(
        client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id]
    )
    _entregar(client, aluno_maior, atividade["id"])
    _editar(client, professor, atividade["id"], aluno_ids=[outro_aluno.id])
    assert _ids(_listar(client, aluno_maior, situacao="realizadas")) == [
        atividade["id"]
    ]
    assert _detalhe(client, aluno_maior, atividade["id"]).status_code == 200

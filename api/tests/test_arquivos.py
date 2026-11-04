from datetime import timedelta

import pytest
from sqlalchemy import select

from src.core.drive import FalhaDrive
from src.core.security import agora
from src.models.arquivo import Arquivo, StatusArquivo
from src.services import arquivo_service
from tests.conftest import cabecalho

ROTA = "/v1/arquivos"
PDF = "application/pdf"
LIMITE = arquivo_service.TAMANHO_MAXIMO_BYTES


def _abrir(client, usuario, **campos):
    dados = {"nome": "aula.pdf", "tipo_mime": PDF, "tamanho": 1024, **campos}
    return client.post(f"{ROTA}/sessao", json=dados, headers=cabecalho(usuario))


def _sessao(client, usuario, **campos):
    resposta = _abrir(client, usuario, **campos)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()["dados"]["arquivo_id"]


def _confirmar(client, usuario, arquivo_id, drive_file_id):
    return client.post(
        f"{ROTA}/{arquivo_id}/confirmar",
        json={"drive_file_id": drive_file_id},
        headers=cabecalho(usuario),
    )


def _tipos_de_erro(resposta):
    assert resposta.status_code == 422, resposta.json()
    return [(erro["local"], erro["tipo"]) for erro in resposta.json()["erros"]]


def _arquivo(sessao, arquivo_id):
    sessao.expire_all()
    return sessao.get(Arquivo, arquivo_id)


@pytest.mark.parametrize(
    ("metodo", "rota", "corpo"),
    [
        ("post", f"{ROTA}/sessao", {}),
        ("post", f"{ROTA}/1/confirmar", {}),
        ("delete", f"{ROTA}/1", None),
    ],
)
def test_arquivos_exigem_login(client, metodo, rota, corpo):
    assert client.request(metodo, rota, json=corpo).status_code == 401


def test_caminho_completo(client, professor, drive, sessao):
    resposta = _abrir(client, professor)
    assert resposta.status_code == 201
    dados = resposta.json()["dados"]
    assert dados["url_upload"] == f"https://drive.exemplo/upload/{dados['arquivo_id']}"
    assert _arquivo(sessao, dados["arquivo_id"]).status == StatusArquivo.PENDENTE

    drive_file_id = drive.receber(dados["arquivo_id"], tamanho=2048)
    resposta = _confirmar(client, professor, dados["arquivo_id"], drive_file_id)
    assert resposta.status_code == 200
    assert resposta.json()["dados"] == {
        "id": dados["arquivo_id"],
        "nome": "aula.pdf",
        "tipo_mime": PDF,
        "tamanho": 2048,
        "url": f"https://drive.exemplo/ver/{drive_file_id}",
    }
    assert drive.compartilhados == [drive_file_id]
    arquivo = _arquivo(sessao, dados["arquivo_id"])
    assert arquivo.status == StatusArquivo.CONFIRMADO
    assert arquivo.drive_file_id == drive_file_id


def test_aluno_tambem_envia(client, aluno_maior, drive):
    arquivo_id = _sessao(client, aluno_maior)
    resposta = _confirmar(client, aluno_maior, arquivo_id, drive.receber(arquivo_id))
    assert resposta.status_code == 200


@pytest.mark.parametrize(
    ("campos", "campo", "tipo"),
    [
        ({"tipo_mime": "text/html"}, "tipo_mime", "tipo_nao_permitido"),
        ({"tipo_mime": "image/svg+xml"}, "tipo_mime", "tipo_nao_permitido"),
        ({"tamanho": LIMITE + 1}, "tamanho", "arquivo_muito_grande"),
    ],
)
def test_sessao_recusada(client, professor, drive, campos, campo, tipo):
    resposta = _abrir(client, professor, **campos)
    assert _tipos_de_erro(resposta) == [(["body", campo], tipo)]
    assert drive.sessoes == {}


def test_arquivo_de_5_mb_exatos_e_aceito(client, professor):
    _sessao(client, professor, tamanho=LIMITE)


def test_limite_de_arquivos_sem_vinculo(client, professor, arquivo_confirmado):
    for _ in range(arquivo_service.MAXIMO_SEM_VINCULO_POR_USUARIO - 1):
        _sessao(client, professor)
    arquivo_id = arquivo_confirmado(professor)
    assert _abrir(client, professor).status_code == 409
    # Descartar libera espaço.
    client.delete(f"{ROTA}/{arquivo_id}", headers=cabecalho(professor))
    assert _abrir(client, professor).status_code == 201


def test_drive_fora_do_ar_nao_grava_nada(client, professor, drive, sessao):
    drive.falhar = True
    assert _abrir(client, professor).status_code == 503
    assert (
        sessao.scalars(
            select(Arquivo).where(Arquivo.enviado_por_id == professor.id)
        ).all()
        == []
    )


def test_so_origem_conhecida_vai_para_a_sessao(client, professor, drive, monkeypatch):
    client.post(
        f"{ROTA}/sessao",
        json={"nome": "a.pdf", "tipo_mime": PDF, "tamanho": 1},
        headers={**cabecalho(professor), "Origin": "https://malicioso.exemplo"},
    )
    client.post(
        f"{ROTA}/sessao",
        json={"nome": "b.pdf", "tipo_mime": PDF, "tamanho": 1},
        headers={**cabecalho(professor), "Origin": "http://localhost:8081"},
    )
    assert [item["origem"] for item in drive.sessoes.values()] == [
        None,
        "http://localhost:8081",
    ]


def test_confirmar_de_novo_nao_repete_a_chamada(client, professor, drive):
    arquivo_id = _sessao(client, professor)
    drive_file_id = drive.receber(arquivo_id)
    primeira = _confirmar(client, professor, arquivo_id, drive_file_id)
    segunda = _confirmar(client, professor, arquivo_id, drive_file_id)
    assert segunda.status_code == 200
    assert segunda.json()["dados"] == primeira.json()["dados"]
    assert drive.compartilhados == [drive_file_id]


def test_confirmar_depois_de_falha_funciona(client, professor, drive):
    arquivo_id = _sessao(client, professor)
    drive_file_id = drive.receber(arquivo_id)
    drive.falhar = True
    assert _confirmar(client, professor, arquivo_id, drive_file_id).status_code == 503
    drive.falhar = False
    assert _confirmar(client, professor, arquivo_id, drive_file_id).status_code == 200


def test_arquivo_trocado_nao_confirma_nem_apaga(client, professor, drive, sessao):
    primeiro = _sessao(client, professor)
    segundo = _sessao(client, professor)
    do_segundo = drive.receber(segundo)
    resposta = _confirmar(client, professor, primeiro, do_segundo)
    assert _tipos_de_erro(resposta) == [
        (["body", "drive_file_id"], "arquivo_nao_enviado")
    ]
    assert drive.apagados == []
    assert _arquivo(sessao, primeiro).status == StatusArquivo.PENDENTE


def test_nao_enviado_ainda(client, professor):
    arquivo_id = _sessao(client, professor)
    resposta = _confirmar(client, professor, arquivo_id, "nao-existe")
    assert _tipos_de_erro(resposta) == [
        (["body", "drive_file_id"], "arquivo_nao_enviado")
    ]


@pytest.mark.parametrize(
    ("real", "tipo"),
    [
        ({"tamanho": LIMITE + 1}, "arquivo_muito_grande"),
        ({"tipo_mime": "text/html"}, "tipo_nao_permitido"),
    ],
)
def test_conteudo_real_fora_do_limite_e_recusado(
    client, professor, drive, sessao, real, tipo
):
    arquivo_id = _sessao(client, professor)
    drive_file_id = drive.receber(arquivo_id, **real)
    resposta = _confirmar(client, professor, arquivo_id, drive_file_id)
    assert _tipos_de_erro(resposta)[0][1] == tipo
    assert drive.compartilhados == []
    arquivo = _arquivo(sessao, arquivo_id)
    assert arquivo.status == StatusArquivo.REMOVER
    assert arquivo.drive_file_id == drive_file_id

    assert arquivo_service.limpar(sessao, drive) == 1
    assert drive.apagados == [drive_file_id]


def test_arquivo_de_outro_usuario(client, professor, outro_professor, drive):
    arquivo_id = _sessao(client, professor)
    drive_file_id = drive.receber(arquivo_id)
    assert (
        _confirmar(client, outro_professor, arquivo_id, drive_file_id).status_code
        == 404
    )
    resposta = client.delete(f"{ROTA}/{arquivo_id}", headers=cabecalho(outro_professor))
    assert resposta.status_code == 404


def test_drive_file_id_com_caracteres_invalidos(client, professor):
    arquivo_id = _sessao(client, professor)
    assert _confirmar(client, professor, arquivo_id, "../x").status_code == 422


def test_descartar(client, professor, arquivo_confirmado, sessao):
    arquivo_id = arquivo_confirmado(professor)
    rota = f"{ROTA}/{arquivo_id}"
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 200
    assert _arquivo(sessao, arquivo_id).status == StatusArquivo.REMOVER
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 404


# --- limpeza ---


def _daqui_a(monkeypatch, **tempo):
    momento = agora() + timedelta(**tempo)
    monkeypatch.setattr(arquivo_service, "agora", lambda: momento)


def test_pendente_recente_fica(client, professor, drive, sessao):
    _sessao(client, professor)
    assert arquivo_service.limpar(sessao, drive) == 0


def test_pendente_antigo_sai_mesmo_com_o_envio_feito(
    client, professor, drive, sessao, monkeypatch
):
    arquivo_id = _sessao(client, professor)
    drive_file_id = drive.receber(arquivo_id)
    _daqui_a(monkeypatch, hours=1, minutes=1)
    assert arquivo_service.limpar(sessao, drive) == 1
    assert drive.apagados == [drive_file_id]
    assert _arquivo(sessao, arquivo_id).deletado_em is not None


def test_confirmado_sem_vinculo_sai_em_24_horas(
    client, professor, arquivo_confirmado, drive, sessao, monkeypatch
):
    arquivo_id = arquivo_confirmado(professor)
    _daqui_a(monkeypatch, hours=23)
    assert arquivo_service.limpar(sessao, drive) == 0
    _daqui_a(monkeypatch, hours=25)
    assert arquivo_service.limpar(sessao, drive) == 1
    assert _arquivo(sessao, arquivo_id).deletado_em is not None


def test_limite_por_execucao(client, professor, drive, sessao, monkeypatch):
    for _ in range(3):
        _sessao(client, professor)
    _daqui_a(monkeypatch, hours=2)
    assert arquivo_service.limpar(sessao, drive, limite=2) == 2
    assert arquivo_service.limpar(sessao, drive, limite=2) == 1
    assert arquivo_service.limpar(sessao, drive, limite=2) == 0


def test_para_na_primeira_falha(client, professor, drive, sessao, monkeypatch):
    for _ in range(3):
        drive.receber(_sessao(client, professor))
    chamadas = []

    def apagar(drive_file_id):
        chamadas.append(drive_file_id)
        raise FalhaDrive("fora do ar")

    monkeypatch.setattr(drive, "apagar", apagar)
    _daqui_a(monkeypatch, hours=2)
    assert arquivo_service.limpar(sessao, drive) == 0
    assert len(chamadas) == 1


def test_erro_inesperado_nao_derruba_a_tarefa(sessao, drive, monkeypatch):
    def quebrar(*_, **__):
        raise RuntimeError("inesperado")

    monkeypatch.setattr(arquivo_service, "limpar", quebrar)
    assert arquivo_service.limpar_sem_falhar(sessao, drive) == 0

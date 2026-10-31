from datetime import timedelta

import pytest
from sqlalchemy import func, select

from src.core.push import FalhaPush, Recibo
from src.core.security import agora
from src.models.notificacao import Dispositivo, EnvioPush, Notificacao, StatusEnvio
from src.schemas.aluno import hoje
from src.services import aula_service, notificacao_service, recado_service
from tests.conftest import cabecalho
from tests.test_aulas import _aula, _horario

TEXTO = "**Aula de sábado** cancelada.\n\n# Reposição na terça"


def _token(usuario, sufixo=""):
    return f"ExponentPushToken[u{usuario.id}{sufixo}]"


def _registrar(client, usuario, sufixo=""):
    resposta = client.post(
        "/v1/dispositivos",
        json={"token": _token(usuario, sufixo)},
        headers=cabecalho(usuario),
    )
    assert resposta.status_code == 200


def _recado(client, professor, **campos):
    dados = {"conteudo": TEXTO, "todos_alunos": True, **campos}
    resposta = client.post("/v1/recados", json=dados, headers=cabecalho(professor))
    assert resposta.status_code == 201
    return resposta.json()["dados"]


def _notificacao(sessao, recado):
    return sessao.scalar(
        select(Notificacao).where(Notificacao.referencia_id == recado["id"])
    )


def _envios(sessao):
    return sessao.scalars(select(EnvioPush).order_by(EnvioPush.id)).all()


def _avancar(monkeypatch, dias=0, minutos=0, momento=None):
    """Simula a tarefa agendada rodando no futuro."""
    if momento is None:
        momento = agora() + timedelta(days=dias, minutes=minutos)
    data = momento.astimezone(recado_service.HORARIO_DE_BRASILIA).date()
    monkeypatch.setattr(notificacao_service, "agora", lambda: momento)
    monkeypatch.setattr(recado_service, "hoje", lambda: data)


def _avancar_ate_o_aviso(monkeypatch, data):
    # A partir do horário do aviso, e não de agora: senão, rodando antes das
    # 7h, o momento simulado ainda não alcança o aviso.
    _avancar(monkeypatch, momento=recado_service._momento_do_aviso(data))


@pytest.fixture
def aluno_fora(criar_aluno_com_perfil):
    return criar_aluno_com_perfil("fora@exemplo.com", anos=16)


# --- envio na criação ---


def test_recado_de_hoje_avisa_os_destinatarios(
    client, professor, aluno_maior, aluno_fora, enviador_push, sessao
):
    for usuario in (professor, aluno_maior, aluno_fora):
        _registrar(client, usuario)
    recado = _recado(client, professor, todos_alunos=False, aluno_ids=[aluno_maior.id])

    assert enviador_push.tokens() == [_token(aluno_maior)]
    mensagem = enviador_push.mensagens[0]
    assert mensagem.titulo == "Novo recado de Usuário de Teste"
    assert mensagem.corpo == "Aula de sábado cancelada. Reposição na terça"
    assert mensagem.dados == {"tipo": "recado", "recado_id": recado["id"]}

    assert _notificacao(sessao, recado).processada_em is not None
    envio = _envios(sessao)[0]
    assert envio.status == StatusEnvio.ENVIADO
    assert envio.ticket_id == f"ticket-{_token(aluno_maior)}"


def test_aviso_segue_a_regra_do_mural(
    client,
    professor,
    outro_professor,
    aluno_maior,
    aluno_menor,
    aluno_fora,
    enviador_push,
):
    for usuario in (aluno_maior, aluno_menor, aluno_fora):
        _registrar(client, usuario)
    _registrar(client, aluno_menor, sufixo="tablet")
    grupo = client.post(
        "/v1/grupos",
        json={"titulo": "Turma A", "aluno_ids": [aluno_menor.id]},
        headers=cabecalho(professor),
    ).json()["dados"]["id"]
    client.post(
        "/v1/grupos",
        json={"titulo": "Outra", "aluno_ids": [aluno_fora.id]},
        headers=cabecalho(outro_professor),
    )

    _recado(client, professor, todos_alunos=False, grupo_ids=[grupo])
    assert sorted(enviador_push.tokens()) == sorted(
        [_token(aluno_menor), _token(aluno_menor, "tablet")]
    )

    enviador_push.mensagens.clear()
    _recado(client, professor, todos_alunos=False, todos_grupos=True)
    assert len(enviador_push.mensagens) == 2  # o aluno_fora é de outro professor

    enviador_push.mensagens.clear()
    _recado(client, professor)
    assert len(enviador_push.mensagens) == 4


def test_recado_sem_dispositivos_e_processado(client, professor, aluno_maior, sessao):
    recado = _recado(client, professor)
    assert _notificacao(sessao, recado).processada_em is not None
    assert _envios(sessao) == []


def test_falha_no_envio_imediato_nao_afeta_a_criacao(
    client, professor, aluno_maior, enviador_push, sessao
):
    _registrar(client, aluno_maior)
    enviador_push.falhar = True
    recado = _recado(client, professor)

    notificacao = _notificacao(sessao, recado)
    assert notificacao.processada_em is None
    assert notificacao.tentativas == 1
    assert notificacao.enviar_em > agora()


def test_envio_imediato_nao_leva_o_resto_da_fila(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    data = hoje() + timedelta(days=1)
    atrasado = _recado(client, professor, data_inicio=data.isoformat())
    _avancar_ate_o_aviso(monkeypatch, data)
    novo = _recado(client, professor)

    assert len(enviador_push.mensagens) == 1
    assert enviador_push.mensagens[0].dados["recado_id"] == novo["id"]
    assert _notificacao(sessao, atrasado).processada_em is None
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 1
    assert len(enviador_push.mensagens) == 2


def test_falha_de_leitura_nao_repete_os_lotes_ja_enviados(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    """O Expo aceita o primeiro lote e a conexão cai no segundo."""
    monkeypatch.setattr(notificacao_service, "MENSAGENS_POR_ENVIO", 1)
    _registrar(client, aluno_maior, "a")
    _registrar(client, aluno_maior, "b")
    enviar_original = enviador_push.enviar
    chamadas = []

    def enviar(mensagens):
        chamadas.append(mensagens)
        if len(chamadas) == 2:
            raise FalhaPush("conexão caiu ao ler a resposta")
        return enviar_original(mensagens)

    monkeypatch.setattr(enviador_push, "enviar", enviar)
    recado = _recado(client, professor)

    assert len(_envios(sessao)) == 1
    assert _notificacao(sessao, recado).tentativas == 1

    monkeypatch.setattr(enviador_push, "enviar", enviar_original)
    _avancar(monkeypatch, minutos=6)
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 1
    assert enviador_push.tokens() == [
        _token(aluno_maior, "a"),
        _token(aluno_maior, "b"),
    ]


# --- tarefa agendada ---


def test_recado_futuro_e_avisado_no_dia(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    data = hoje() + timedelta(days=2)
    recado = _recado(client, professor, data_inicio=data.isoformat())
    assert enviador_push.mensagens == []
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 0

    _avancar_ate_o_aviso(monkeypatch, data)
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 1
    assert enviador_push.tokens() == [_token(aluno_maior)]
    assert _notificacao(sessao, recado).processada_em is not None


def test_horario_do_aviso_agendado(client, professor, sessao):
    data = hoje() + timedelta(days=3)
    recado = _recado(client, professor, data_inicio=data.isoformat())
    enviar_em = _notificacao(sessao, recado).enviar_em
    assert enviar_em == recado_service._momento_do_aviso(data)
    assert enviar_em.astimezone(recado_service.HORARIO_DE_BRASILIA).hour == 7


def test_editar_a_data_reagenda_o_aviso(client, professor, sessao):
    recado = _recado(
        client, professor, data_inicio=(hoje() + timedelta(days=2)).isoformat()
    )
    nova = hoje() + timedelta(days=5)
    client.patch(
        f"/v1/recados/{recado['id']}",
        json={"data_inicio": nova.isoformat()},
        headers=cabecalho(professor),
    )
    sessao.expire_all()
    assert _notificacao(sessao, recado).enviar_em == recado_service._momento_do_aviso(
        nova
    )


def test_editar_recado_ja_avisado_nao_avisa_de_novo(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    recado = _recado(client, professor)
    client.patch(
        f"/v1/recados/{recado['id']}",
        json={"conteudo": "Texto novo", "data_inicio": hoje().isoformat()},
        headers=cabecalho(professor),
    )
    _avancar(monkeypatch, minutos=1)
    notificacao_service.processar_pendentes(sessao, enviador_push)
    assert len(enviador_push.mensagens) == 1


def test_recado_excluido_antes_do_aviso_e_descartado(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    data = hoje() + timedelta(days=1)
    recado = _recado(client, professor, data_inicio=data.isoformat())
    client.delete(f"/v1/recados/{recado['id']}", headers=cabecalho(professor))

    _avancar_ate_o_aviso(monkeypatch, data)
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 1
    assert enviador_push.mensagens == []
    assert _notificacao(sessao, recado).processada_em is not None


def test_processar_de_novo_nao_repete_o_envio(
    client, professor, aluno_maior, enviador_push, sessao
):
    _registrar(client, aluno_maior)
    _recado(client, professor)
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 0
    assert len(enviador_push.mensagens) == 1


def test_nova_tentativa_depois_de_falha(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    enviador_push.falhar = True
    recado = _recado(client, professor)
    # Na mesma execução, a notificação que falhou não é tentada de novo.
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 0
    assert _notificacao(sessao, recado).tentativas == 1

    enviador_push.falhar = False
    _avancar(monkeypatch, minutos=10)
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 1
    assert enviador_push.tokens() == [_token(aluno_maior)]


def test_desiste_depois_do_maximo_de_tentativas(
    client, professor, aluno_maior, enviador_push, sessao
):
    _registrar(client, aluno_maior)
    enviador_push.falhar = True
    recado = _recado(client, professor)
    notificacao = _notificacao(sessao, recado)
    notificacao.tentativas = notificacao_service.MAXIMO_TENTATIVAS
    notificacao.enviar_em = agora() - timedelta(minutes=1)
    sessao.commit()

    enviador_push.falhar = False
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 0
    assert enviador_push.mensagens == []


def test_token_nao_registrado_desativa_o_dispositivo(
    client, professor, aluno_maior, aluno_menor, enviador_push, sessao
):
    _registrar(client, aluno_maior)
    _registrar(client, aluno_menor)
    enviador_push.erros[_token(aluno_maior)] = "DeviceNotRegistered"
    _recado(client, professor)

    por_token = {
        dispositivo.token: dispositivo
        for dispositivo in sessao.scalars(select(Dispositivo))
    }
    assert por_token[_token(aluno_maior)].deletado_em is not None
    assert por_token[_token(aluno_menor)].deletado_em is None
    status = sorted(envio.status for envio in _envios(sessao))
    assert status == [StatusEnvio.ENVIADO, StatusEnvio.ERRO]


# --- recibos ---


def test_confere_os_recibos(
    client, professor, aluno_maior, aluno_menor, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    _registrar(client, aluno_menor)
    _recado(client, professor)
    ticket_maior = f"ticket-{_token(aluno_maior)}"
    ticket_menor = f"ticket-{_token(aluno_menor)}"
    enviador_push.recibos = {
        ticket_maior: Recibo(ok=True),
        ticket_menor: Recibo(ok=False, erro="DeviceNotRegistered"),
    }

    # Antes de 15 minutos, os recibos ainda não são consultados.
    assert notificacao_service.conferir_recibos(sessao, enviador_push) == 0
    assert enviador_push.consultas == []

    _avancar(monkeypatch, minutos=20)
    assert notificacao_service.conferir_recibos(sessao, enviador_push) == 2
    envios = {envio.ticket_id: envio for envio in _envios(sessao)}
    assert envios[ticket_maior].status == StatusEnvio.OK
    assert envios[ticket_menor].status == StatusEnvio.ERRO
    assert envios[ticket_menor].erro == "DeviceNotRegistered"
    assert all(envio.verificado_em is not None for envio in envios.values())
    sessao.expire_all()
    dispositivo = sessao.scalar(
        select(Dispositivo).where(Dispositivo.token == _token(aluno_menor))
    )
    assert dispositivo.deletado_em is not None


def test_recibo_que_nao_chega(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    _recado(client, professor)

    _avancar(monkeypatch, minutos=20)
    assert notificacao_service.conferir_recibos(sessao, enviador_push) == 0
    assert _envios(sessao)[0].status == StatusEnvio.ENVIADO

    _avancar(monkeypatch, dias=2)
    assert notificacao_service.conferir_recibos(sessao, enviador_push) == 1
    assert _envios(sessao)[0].status == StatusEnvio.SEM_RECIBO


# --- texto ---


@pytest.mark.parametrize(
    ("conteudo", "esperado"),
    [
        ("**Oi**,  _turma_!\n\n> citação `código`", "Oi, turma! citação código"),
        ("a" * 200, "a" * 119 + "…"),
    ],
)
def test_resumo_do_recado(conteudo, esperado):
    assert recado_service._resumo(conteudo) == esperado


# --- aulas ---


def _notificacoes_da_aula(sessao, aula_id):
    return sessao.scalars(
        select(Notificacao)
        .where(
            Notificacao.referencia_id == aula_id,
            Notificacao.tipo.like("aula%"),
            Notificacao.deletado_em.is_(None),
        )
        .order_by(Notificacao.enviar_em)
    ).all()


def _ate(monkeypatch, momento):
    """Simula a tarefa agendada rodando em `momento`."""
    monkeypatch.setattr(notificacao_service, "agora", lambda: momento)
    monkeypatch.setattr(aula_service, "agora", lambda: momento)


def test_aula_agenda_os_tres_lembretes(client, professor, aluno_maior, sessao):
    aula = _aula(client, professor, [aluno_maior.id], dias=10)
    inicio = _horario(10)
    assert [
        (notificacao.tipo, notificacao.enviar_em)
        for notificacao in _notificacoes_da_aula(sessao, aula["id"])
    ] == [
        ("aula_lembrete_semana", inicio - timedelta(weeks=1)),
        ("aula_lembrete_dia", inicio - timedelta(days=1)),
        ("aula_lembrete_30min", inicio - timedelta(minutes=30)),
    ]


def test_lembretes_que_ja_passaram_nao_sao_agendados(
    client, professor, aluno_maior, sessao
):
    aula = _aula(client, professor, [aluno_maior.id], dias=2)
    tipos = [n.tipo for n in _notificacoes_da_aula(sessao, aula["id"])]
    assert tipos == ["aula_lembrete_dia", "aula_lembrete_30min"]


def test_lembrete_vai_para_os_alunos_ativos(
    client, professor, aluno_maior, aluno_fora, enviador_push, sessao, monkeypatch
):
    for usuario in (professor, aluno_maior, aluno_fora):
        _registrar(client, usuario)
    aula = _aula(client, professor, [aluno_maior.id, aluno_fora.id], dias=2)
    client.post(
        f"/v1/agenda/{aula['id']}/cancelar",
        json={},
        headers=cabecalho(aluno_fora),
    )
    enviador_push.mensagens.clear()  # o aviso do cancelamento ao professor

    _ate(monkeypatch, _horario(2) - timedelta(minutes=30))
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 2
    assert enviador_push.tokens() == [_token(aluno_maior), _token(aluno_maior)]
    dia, trinta = enviador_push.mensagens
    assert dia.titulo == "Aula amanhã: Espanhol"
    assert trinta.titulo == "Aula em 30 minutos: Espanhol"
    assert trinta.corpo == (
        f"{aula_service.formatar_horario(_horario(2))}, com Usuário de Teste"
    )
    assert trinta.dados == {"tipo": "aula_lembrete_30min", "aula_id": aula["id"]}


def test_mudar_o_horario_refaz_os_lembretes(client, professor, aluno_maior, sessao):
    aula = _aula(client, professor, [aluno_maior.id], dias=10)
    novo = _horario(3, hora=18)
    client.patch(
        f"/v1/aulas/{aula['id']}",
        json={
            "inicio": novo.isoformat(),
            "fim": (novo + timedelta(hours=1)).isoformat(),
        },
        headers=cabecalho(professor),
    )
    sessao.expire_all()
    assert [
        (notificacao.tipo, notificacao.enviar_em)
        for notificacao in _notificacoes_da_aula(sessao, aula["id"])
    ] == [
        ("aula_lembrete_dia", novo - timedelta(days=1)),
        ("aula_lembrete_30min", novo - timedelta(minutes=30)),
    ]


def test_aula_cancelada_avisa_e_descarta_os_lembretes(
    client, professor, aluno_maior, enviador_push, sessao, monkeypatch
):
    _registrar(client, aluno_maior)
    aula = _aula(client, professor, [aluno_maior.id], dias=2)
    client.post(
        f"/v1/aulas/{aula['id']}/cancelar",
        json={"motivo": "Imprevisto"},
        headers=cabecalho(professor),
    )
    (mensagem,) = enviador_push.mensagens
    assert mensagem.titulo == "Aula cancelada: Espanhol"
    assert mensagem.corpo == (
        f"A aula de {aula_service.formatar_horario(_horario(2))} foi cancelada. "
        "Motivo: Imprevisto"
    )
    assert mensagem.dados == {"tipo": "aula_cancelada", "aula_id": aula["id"]}

    _ate(monkeypatch, _horario(2) - timedelta(minutes=1))
    assert notificacao_service.processar_pendentes(sessao, enviador_push) == 0
    assert len(enviador_push.mensagens) == 1


def test_serie_cancelada_gera_um_aviso_so(
    client, professor, aluno_maior, enviador_push, sessao
):
    _registrar(client, aluno_maior)
    aula = _aula(
        client,
        professor,
        [aluno_maior.id],
        repetir_semanalmente=True,
        repetir_ate=(hoje() + timedelta(weeks=4)).isoformat(),
    )
    client.post(
        f"/v1/aulas/{aula['id']}/cancelar",
        params={"escopo": "esta_e_seguintes"},
        json={},
        headers=cabecalho(professor),
    )
    (mensagem,) = enviador_push.mensagens
    assert mensagem.titulo == "Aulas canceladas: Espanhol"
    assert mensagem.dados == {"tipo": "aulas_canceladas", "aula_id": aula["id"]}
    pendentes = sessao.scalar(
        select(func.count())
        .select_from(Notificacao)
        .where(
            Notificacao.tipo.like("aula_lembrete%"),
            Notificacao.processada_em.is_(None),
            Notificacao.deletado_em.is_(None),
        )
    )
    assert pendentes == 0


def test_aluno_que_cancela_avisa_o_professor(
    client, professor, aluno_maior, enviador_push
):
    _registrar(client, professor)
    _registrar(client, aluno_maior)
    aula = _aula(client, professor, [aluno_maior.id])
    client.post(
        f"/v1/agenda/{aula['id']}/cancelar",
        json={"motivo": "Consulta médica"},
        headers=cabecalho(aluno_maior),
    )
    (mensagem,) = enviador_push.mensagens
    assert mensagem.token == _token(professor)
    assert mensagem.titulo == "Aluno de Teste cancelou a aula"
    assert mensagem.corpo == (
        f"Espanhol, {aula_service.formatar_horario(_horario(3))}. "
        "Motivo: Consulta médica"
    )
    assert mensagem.dados == {
        "tipo": "participacao_cancelada",
        "aula_id": aula["id"],
        "aluno_id": aluno_maior.id,
    }

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from src.models.financeiro import (
    Cobranca,
    FrequenciaPlano,
    PlanoCobranca,
    StatusCobranca,
)
from src.models.notificacao import Notificacao, TipoNotificacao
from src.models.professor import Professor
from src.schemas.aluno import hoje
from src.services import financeiro_service
from tests.conftest import cabecalho

ROTA = "/v1/financeiro"


def _plano(**campos) -> PlanoCobranca:
    padrao = {
        "frequencia": FrequenciaPlano.MENSAL,
        "dia_vencimento": 10,
        "inicio": date(2026, 1, 1),
        "fim": None,
    }
    return PlanoCobranca(**{**padrao, **campos})


def _criar_plano(client, professor, aluno, **campos):
    corpo = {
        "aluno_id": aluno.id,
        "descricao": "Mensalidade",
        "valor_centavos": 25000,
        "frequencia": "mensal",
        "dia_vencimento": hoje().day,
        **campos,
    }
    resposta = client.post(f"{ROTA}/planos", json=corpo, headers=cabecalho(professor))
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()["dados"]


def _avulsa(client, professor, aluno, vencimento=None, **campos):
    corpo = {
        "aluno_id": aluno.id,
        "descricao": "Material",
        "valor_centavos": 5000,
        "vencimento": (vencimento or hoje() + timedelta(days=5)).isoformat(),
        **campos,
    }
    resposta = client.post(
        f"{ROTA}/cobrancas", json=corpo, headers=cabecalho(professor)
    )
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()["dados"]


def _cobrancas(sessao, plano_id):
    sessao.expire_all()
    return sessao.scalars(
        select(Cobranca)
        .where(Cobranca.plano_id == plano_id)
        .order_by(Cobranca.vencimento)
    ).all()


def _tipos(resposta):
    return [erro["tipo"] for erro in resposta.json()["erros"]]


# --- datas de vencimento ---


def test_mensal_usa_o_ultimo_dia_dos_meses_curtos():
    plano = _plano(dia_vencimento=31)
    datas = list(
        financeiro_service.vencimentos(plano, date(2026, 1, 1), date(2026, 4, 30))
    )
    assert datas == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    ]


def test_mensal_respeita_inicio_e_fim():
    plano = _plano(inicio=date(2026, 1, 15), fim=date(2026, 3, 9))
    datas = list(
        financeiro_service.vencimentos(plano, date(2026, 1, 1), date(2026, 12, 31))
    )
    # O dia 10 de janeiro é antes do início; o de março, depois do fim.
    assert datas == [date(2026, 2, 10)]


def test_semanal_no_dia_da_semana():
    # 2026-11-02 é segunda; dia 2 é quarta.
    plano = _plano(
        frequencia=FrequenciaPlano.SEMANAL, dia_vencimento=2, inicio=date(2026, 11, 2)
    )
    datas = list(
        financeiro_service.vencimentos(plano, date(2026, 11, 2), date(2026, 11, 20))
    )
    assert datas == [date(2026, 11, 4), date(2026, 11, 11), date(2026, 11, 18)]
    assert all(data.weekday() == 2 for data in datas)


# --- permissões ---


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("post", f"{ROTA}/planos"),
        ("get", f"{ROTA}/planos"),
        ("get", f"{ROTA}/planos/1"),
        ("patch", f"{ROTA}/planos/1"),
        ("delete", f"{ROTA}/planos/1"),
        ("post", f"{ROTA}/cobrancas"),
        ("get", f"{ROTA}/cobrancas"),
        ("get", f"{ROTA}/cobrancas/1"),
        ("patch", f"{ROTA}/cobrancas/1"),
        ("post", f"{ROTA}/cobrancas/1/pagar"),
        ("post", f"{ROTA}/cobrancas/1/reabrir"),
        ("post", f"{ROTA}/cobrancas/1/cancelar"),
        ("get", f"{ROTA}/resumo"),
    ],
)
def test_rotas_sao_do_professor(client, aluno_maior, metodo, rota):
    assert client.request(metodo, rota, json={}).status_code == 401
    resposta = client.request(metodo, rota, json={}, headers=cabecalho(aluno_maior))
    assert resposta.status_code == 403


# --- planos ---


def test_plano_gera_as_cobrancas_dos_proximos_dias(
    client, professor, aluno_maior, sessao
):
    plano = _criar_plano(client, professor, aluno_maior)
    assert plano["aluno_nome"] == aluno_maior.nome_completo
    cobrancas = _cobrancas(sessao, plano["id"])
    # A de hoje e a do mês seguinte, que cabe nos 35 dias de antecedência.
    assert len(cobrancas) == 2
    assert cobrancas[0].vencimento == hoje()
    assert cobrancas[1].vencimento.day <= hoje().day
    assert cobrancas[0].valor_centavos == 25000

    # Rodar de novo não duplica.
    assert financeiro_service.gerar_cobrancas(sessao) == 0
    # Um mês depois, gera a próxima.
    assert financeiro_service.gerar_cobrancas(sessao, hoje() + timedelta(days=31)) == 1


def test_plano_semanal(client, professor, aluno_maior, sessao):
    plano = _criar_plano(
        client,
        professor,
        aluno_maior,
        frequencia="semanal",
        dia_vencimento=hoje().weekday(),
    )
    datas = [cobranca.vencimento for cobranca in _cobrancas(sessao, plano["id"])]
    assert datas == [hoje() + timedelta(weeks=semanas) for semanas in range(6)]


@pytest.mark.parametrize(
    ("campos", "tipo"),
    [
        ({"frequencia": "mensal", "dia_vencimento": 0}, "value_error"),
        ({"frequencia": "semanal", "dia_vencimento": 7}, "value_error"),
        ({"valor_centavos": 0}, "greater_than_equal"),
        ({"valor_centavos": 10_000_001}, "less_than_equal"),
    ],
)
def test_plano_invalido(client, professor, aluno_maior, campos, tipo):
    corpo = {
        "aluno_id": aluno_maior.id,
        "descricao": "Mensalidade",
        "valor_centavos": 25000,
        "frequencia": "mensal",
        "dia_vencimento": 10,
        **campos,
    }
    resposta = client.post(f"{ROTA}/planos", json=corpo, headers=cabecalho(professor))
    assert _tipos(resposta) == [tipo]


def test_plano_com_inicio_no_passado(client, professor, aluno_maior):
    corpo = {
        "aluno_id": aluno_maior.id,
        "descricao": "Mensalidade",
        "valor_centavos": 25000,
        "frequencia": "mensal",
        "dia_vencimento": 10,
        "inicio": (hoje() - timedelta(days=1)).isoformat(),
    }
    resposta = client.post(f"{ROTA}/planos", json=corpo, headers=cabecalho(professor))
    assert _tipos(resposta) == ["inicio_no_passado"]


def test_plano_para_aluno_invalido(client, professor, aluno):
    # `aluno` ainda não concluiu o primeiro acesso.
    corpo = {
        "aluno_id": aluno.id,
        "descricao": "Mensalidade",
        "valor_centavos": 25000,
        "frequencia": "mensal",
        "dia_vencimento": 10,
    }
    resposta = client.post(f"{ROTA}/planos", json=corpo, headers=cabecalho(professor))
    assert _tipos(resposta) == ["aluno_invalido"]


def test_editar_plano_muda_so_as_nao_vencidas(
    client, professor, aluno_maior, sessao, monkeypatch
):
    plano = _criar_plano(client, professor, aluno_maior)
    # Gera a cobrança do mês seguinte também.
    financeiro_service.gerar_cobrancas(sessao, hoje() + timedelta(days=31))
    atual, seguinte, *_ = _cobrancas(sessao, plano["id"])

    # Simula que a de hoje já venceu.
    amanha = hoje() + timedelta(days=1)
    monkeypatch.setattr(financeiro_service, "hoje", lambda: amanha)
    resposta = client.patch(
        f"{ROTA}/planos/{plano['id']}",
        json={"valor_centavos": 30000},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 200
    sessao.expire_all()
    assert sessao.get(Cobranca, atual.id).valor_centavos == 25000
    assert sessao.get(Cobranca, seguinte.id).valor_centavos == 30000


def test_editar_dia_refaz_as_futuras(client, professor, aluno_maior, sessao):
    plano = _criar_plano(
        client,
        professor,
        aluno_maior,
        frequencia="semanal",
        dia_vencimento=hoje().weekday(),
    )
    novo_dia = (hoje().weekday() + 1) % 7
    resposta = client.patch(
        f"{ROTA}/planos/{plano['id']}",
        json={"dia_vencimento": novo_dia},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 200
    datas = [cobranca.vencimento for cobranca in _cobrancas(sessao, plano["id"])]
    assert datas and all(data.weekday() == novo_dia for data in datas)

    resposta = client.patch(
        f"{ROTA}/planos/{plano['id']}",
        json={"dia_vencimento": 7},
        headers=cabecalho(professor),
    )
    assert _tipos(resposta) == ["plano_invalido"]


def test_encerrar_plano_cancela_as_nao_vencidas(
    client, professor, aluno_maior, sessao, monkeypatch
):
    plano = _criar_plano(client, professor, aluno_maior)
    financeiro_service.gerar_cobrancas(sessao, hoje() + timedelta(days=31))
    atual, seguinte, *_ = _cobrancas(sessao, plano["id"])

    amanha = hoje() + timedelta(days=1)
    monkeypatch.setattr(financeiro_service, "hoje", lambda: amanha)
    rota = f"{ROTA}/planos/{plano['id']}"
    assert client.delete(rota, headers=cabecalho(professor)).status_code == 200
    sessao.expire_all()
    # A de hoje venceu e segue devida; a do mês seguinte é cancelada.
    assert sessao.get(Cobranca, atual.id).status == StatusCobranca.PENDENTE
    assert sessao.get(Cobranca, seguinte.id).status == StatusCobranca.CANCELADA
    assert client.get(rota, headers=cabecalho(professor)).status_code == 404
    # Plano encerrado não gera mais.
    assert financeiro_service.gerar_cobrancas(sessao, hoje() + timedelta(days=90)) == 0


# --- cobranças ---


def test_avulsa_e_ciclo_de_baixa(client, professor, aluno_maior):
    cobranca = _avulsa(client, professor, aluno_maior)
    assert cobranca["situacao"] == "pendente"
    assert cobranca["plano_id"] is None
    rota = f"{ROTA}/cobrancas/{cobranca['id']}"
    dela = cabecalho(professor)

    paga = client.post(f"{rota}/pagar", headers=dela).json()["dados"]
    assert paga["situacao"] == "paga"
    assert paga["paga_em"] is not None
    assert client.post(f"{rota}/pagar", headers=dela).status_code == 409
    assert client.post(f"{rota}/cancelar", headers=dela).status_code == 409
    assert (
        client.patch(rota, json={"valor_centavos": 1}, headers=dela).status_code == 409
    )

    reaberta = client.post(f"{rota}/reabrir", headers=dela).json()["dados"]
    assert reaberta["situacao"] == "pendente"
    assert reaberta["paga_em"] is None
    assert client.post(f"{rota}/reabrir", headers=dela).status_code == 409

    cancelada = client.post(f"{rota}/cancelar", headers=dela).json()["dados"]
    assert cancelada["situacao"] == "cancelada"


def test_pagar_com_data_informada(client, professor, aluno_maior):
    cobranca = _avulsa(client, professor, aluno_maior)
    resposta = client.post(
        f"{ROTA}/cobrancas/{cobranca['id']}/pagar",
        json={"paga_em": "2026-11-05T10:00:00-03:00"},
        headers=cabecalho(professor),
    )
    assert resposta.json()["dados"]["paga_em"].startswith("2026-11-05T13:00:00")


def test_situacao_vencida_e_filtros(client, professor, aluno_maior, monkeypatch):
    ontem = hoje() - timedelta(days=1)
    vencida = _avulsa(client, professor, aluno_maior, vencimento=ontem)
    assert vencida["situacao"] == "vencida"
    futura = _avulsa(client, professor, aluno_maior)
    paga = _avulsa(client, professor, aluno_maior)
    client.post(f"{ROTA}/cobrancas/{paga['id']}/pagar", headers=cabecalho(professor))

    def ids(**parametros):
        resposta = client.get(
            f"{ROTA}/cobrancas", params=parametros, headers=cabecalho(professor)
        )
        return [item["id"] for item in resposta.json()["dados"]["itens"]]

    assert ids(situacao="vencida") == [vencida["id"]]
    assert ids(situacao="pendente") == [futura["id"]]
    assert ids(situacao="paga") == [paga["id"]]
    assert ids(de=hoje().isoformat()) == [futura["id"], paga["id"]]
    assert ids(aluno_id=aluno_maior.id) == [vencida["id"], futura["id"], paga["id"]]
    resposta = client.get(
        f"{ROTA}/cobrancas",
        params={"situacao": "atrasada"},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 422


def test_editar_vencimento_reagenda_os_avisos(client, professor, aluno_maior, sessao):
    cobranca = _avulsa(client, professor, aluno_maior)
    novo = hoje() + timedelta(days=20)
    resposta = client.patch(
        f"{ROTA}/cobrancas/{cobranca['id']}",
        json={"vencimento": novo.isoformat()},
        headers=cabecalho(professor),
    )
    assert resposta.json()["dados"]["vencimento"] == novo.isoformat()
    ativas = sessao.scalars(
        select(Notificacao).where(
            Notificacao.referencia_id == cobranca["id"],
            Notificacao.tipo == TipoNotificacao.COBRANCA_VENCE_HOJE,
            Notificacao.deletado_em.is_(None),
        )
    ).all()
    assert len(ativas) == 1
    assert (
        ativas[0].enviar_em.astimezone(financeiro_service.HORARIO_DE_BRASILIA).date()
        == novo
    )


def test_resumo_do_mes(client, professor, aluno_maior):
    hoje_ = hoje()
    vencida = _avulsa(
        client,
        professor,
        aluno_maior,
        vencimento=hoje_.replace(day=1) - timedelta(days=1),
    )
    _avulsa(client, professor, aluno_maior, vencimento=hoje_, valor_centavos=1000)
    paga = _avulsa(
        client, professor, aluno_maior, vencimento=hoje_, valor_centavos=2000
    )
    client.post(f"{ROTA}/cobrancas/{paga['id']}/pagar", headers=cabecalho(professor))
    cancelada = _avulsa(
        client, professor, aluno_maior, vencimento=hoje_, valor_centavos=4000
    )
    client.post(
        f"{ROTA}/cobrancas/{cancelada['id']}/cancelar", headers=cabecalho(professor)
    )

    resumo = client.get(f"{ROTA}/resumo", headers=cabecalho(professor)).json()["dados"]
    assert resumo == {
        "mes": hoje_.strftime("%Y-%m"),
        "recebido_centavos": 2000,
        "pendente_centavos": 1000,
        "vencido_centavos": 0,
    }
    mes_anterior = (hoje_.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    resumo = client.get(
        f"{ROTA}/resumo", params={"mes": mes_anterior}, headers=cabecalho(professor)
    ).json()["dados"]
    assert resumo["vencido_centavos"] == vencida["valor_centavos"]
    assert (
        client.get(
            f"{ROTA}/resumo", params={"mes": "2026-13"}, headers=cabecalho(professor)
        ).status_code
        == 422
    )


# --- outro professor ---


def test_professor_nao_mexe_no_financeiro_de_outro(
    client, professor, outro_professor, aluno_maior
):
    plano = _criar_plano(client, professor, aluno_maior)
    cobranca = _avulsa(client, professor, aluno_maior)
    dele = cabecalho(outro_professor)
    rota_plano = f"{ROTA}/planos/{plano['id']}"
    rota_cobranca = f"{ROTA}/cobrancas/{cobranca['id']}"
    assert client.get(rota_plano, headers=dele).status_code == 404
    assert (
        client.patch(rota_plano, json={"valor_centavos": 1}, headers=dele).status_code
        == 404
    )
    assert client.delete(rota_plano, headers=dele).status_code == 404
    assert client.get(rota_cobranca, headers=dele).status_code == 404
    assert (
        client.patch(
            rota_cobranca, json={"valor_centavos": 1}, headers=dele
        ).status_code
        == 404
    )
    for acao in ("pagar", "reabrir", "cancelar"):
        assert client.post(f"{rota_cobranca}/{acao}", headers=dele).status_code == 404
    assert client.get(f"{ROTA}/planos", headers=dele).json()["dados"]["total"] == 0
    assert client.get(f"{ROTA}/cobrancas", headers=dele).json()["dados"]["total"] == 0
    resumo = client.get(f"{ROTA}/resumo", headers=dele).json()["dados"]
    assert resumo["pendente_centavos"] == 0


# --- avisos ---


def _avisos(sessao, cobranca_id):
    return {
        notificacao.tipo: notificacao.enviar_em
        for notificacao in sessao.scalars(
            select(Notificacao).where(
                Notificacao.referencia_id == cobranca_id,
                Notificacao.tipo.in_(
                    [
                        *financeiro_service.LEMBRETES,
                        TipoNotificacao.COBRANCA_VENCIDA,
                        TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR,
                    ]
                ),
                Notificacao.deletado_em.is_(None),
            )
        )
    }


def test_avisos_agendados(client, professor, aluno_maior, sessao):
    vencimento = hoje() + timedelta(days=45)
    cobranca = _avulsa(client, professor, aluno_maior, vencimento=vencimento)
    avisos = _avisos(sessao, cobranca["id"])
    brasilia = financeiro_service.HORARIO_DE_BRASILIA
    esperado = {
        TipoNotificacao.COBRANCA_VENCE_EM_1_MES: financeiro_service._um_mes_antes(
            vencimento
        ),
        TipoNotificacao.COBRANCA_VENCE_EM_1_SEMANA: vencimento - timedelta(weeks=1),
        TipoNotificacao.COBRANCA_VENCE_HOJE: vencimento,
        TipoNotificacao.COBRANCA_VENCIDA: vencimento + timedelta(days=1),
        TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR: vencimento + timedelta(days=1),
    }
    assert {
        tipo: momento.astimezone(brasilia).date() for tipo, momento in avisos.items()
    } == esperado
    assert all(momento.astimezone(brasilia).hour == 9 for momento in avisos.values())


def test_vencida_ja_no_passado_so_agenda_o_atraso(
    client, professor, aluno_maior, sessao
):
    cobranca = _avulsa(
        client, professor, aluno_maior, vencimento=hoje() - timedelta(days=5)
    )
    assert set(_avisos(sessao, cobranca["id"])) == {
        TipoNotificacao.COBRANCA_VENCIDA,
        TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR,
    }


def test_baixa_cancela_os_avisos(client, professor, aluno_maior, sessao):
    cobranca = _avulsa(client, professor, aluno_maior)
    client.post(
        f"{ROTA}/cobrancas/{cobranca['id']}/pagar", headers=cabecalho(professor)
    )
    assert _avisos(sessao, cobranca["id"]) == {}


def test_conteudo_dos_avisos(client, professor, aluno_maior, sessao):
    cobranca = _avulsa(client, professor, aluno_maior, valor_centavos=123456)
    resolvedores = financeiro_service.RESOLVEDORES
    do_aluno = resolvedores[TipoNotificacao.COBRANCA_VENCE_HOJE](sessao, cobranca["id"])
    assert list(do_aluno.usuario_ids) == [aluno_maior.id]
    assert "R$ 1.234,56" in do_aluno.corpo
    assert professor.nome_completo in do_aluno.corpo
    da_professora = resolvedores[TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR](
        sessao, cobranca["id"]
    )
    assert list(da_professora.usuario_ids) == [professor.id]
    assert aluno_maior.nome_completo in da_professora.titulo

    # Paga, nenhum aviso sai, mesmo que um já estivesse na fila.
    client.post(
        f"{ROTA}/cobrancas/{cobranca['id']}/pagar", headers=cabecalho(professor)
    )
    sessao.expire_all()
    for resolver in resolvedores.values():
        assert resolver(sessao, cobranca["id"]) is None


def test_lembrete_nao_sai_depois_do_vencimento(client, professor, aluno_maior, sessao):
    cobranca = _avulsa(
        client, professor, aluno_maior, vencimento=hoje() - timedelta(days=1)
    )
    resolvedores = financeiro_service.RESOLVEDORES
    assert (
        resolvedores[TipoNotificacao.COBRANCA_VENCE_EM_1_SEMANA](sessao, cobranca["id"])
        is None
    )
    assert (
        resolvedores[TipoNotificacao.COBRANCA_VENCIDA](sessao, cobranca["id"])
        is not None
    )


def test_formatar_valor():
    assert financeiro_service.formatar_valor(5) == "R$ 0,05"
    assert financeiro_service.formatar_valor(1234567) == "R$ 12.345,67"


# --- detalhe do aluno ---


def test_pagamentos_no_detalhe_do_aluno(
    client, professor, outro_professor, aluno_maior
):
    minha = _avulsa(client, professor, aluno_maior)
    _avulsa(client, outro_professor, aluno_maior)
    dados = client.get(
        f"/v1/usuarios/alunos/{aluno_maior.id}", headers=cabecalho(professor)
    ).json()["dados"]
    assert [item["id"] for item in dados["pagamentos"]] == [minha["id"]]
    assert dados["pagamentos"][0]["situacao"] == "pendente"


# --- revisão: datas ao editar o plano ---


def _em(monkeypatch, dia: date) -> None:
    monkeypatch.setattr(financeiro_service, "hoje", lambda: dia)


def _plano_em(sessao, professor, aluno, **campos) -> PlanoCobranca:
    padrao = {
        "aluno_id": aluno.id,
        "descricao": "Mensalidade",
        "valor_centavos": 25000,
        "frequencia": FrequenciaPlano.MENSAL,
        "dia_vencimento": 10,
        "inicio": date(2030, 10, 1),
    }
    plano, _ = financeiro_service.criar_plano(sessao, professor, **{**padrao, **campos})
    return plano


def test_editar_dia_nao_gera_cobranca_ja_vencida(
    sessao, professor, aluno_maior, monkeypatch
):
    _em(monkeypatch, date(2030, 10, 1))
    plano = _plano_em(sessao, professor, aluno_maior)
    _em(monkeypatch, date(2030, 11, 8))
    financeiro_service.gerar_cobrancas(sessao)
    assert [c.vencimento for c in _cobrancas(sessao, plano.id)] == [
        date(2030, 10, 10),
        date(2030, 11, 10),
        date(2030, 12, 10),
    ]

    # Em 08/11, mudar para o dia 5 não pode criar a de 05/11, já vencida.
    financeiro_service.atualizar_plano(
        sessao, professor, plano.id, {"dia_vencimento": 5}
    )
    financeiro_service.gerar_cobrancas(sessao, date(2030, 12, 1))
    assert [c.vencimento for c in _cobrancas(sessao, plano.id)] == [
        date(2030, 10, 10),
        date(2030, 12, 5),
        date(2031, 1, 5),
    ]


def test_editar_dia_nao_cobra_duas_vezes_no_mesmo_mes(
    sessao, professor, aluno_maior, monkeypatch
):
    _em(monkeypatch, date(2030, 11, 8))
    plano = _plano_em(sessao, professor, aluno_maior, inicio=date(2030, 11, 8))
    adiantada, _ = _cobrancas(sessao, plano.id)
    financeiro_service.pagar(sessao, professor, adiantada.id)

    # A de novembro já foi paga: o dia novo só vale a partir de dezembro.
    financeiro_service.atualizar_plano(
        sessao, professor, plano.id, {"dia_vencimento": 15}
    )
    financeiro_service.gerar_cobrancas(sessao, date(2030, 12, 10))
    assert [c.vencimento for c in _cobrancas(sessao, plano.id)] == [
        date(2030, 11, 10),
        date(2030, 12, 15),
    ]


def test_vencimento_repetido_no_plano(client, professor, aluno_maior, sessao):
    plano = _criar_plano(
        client,
        professor,
        aluno_maior,
        frequencia="semanal",
        dia_vencimento=hoje().weekday(),
    )
    primeira, segunda, *_ = _cobrancas(sessao, plano["id"])
    resposta = client.patch(
        f"{ROTA}/cobrancas/{segunda.id}",
        json={"vencimento": primeira.vencimento.isoformat()},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 409
    sessao.expire_all()
    assert sessao.get(Cobranca, segunda.id).vencimento == segunda.vencimento


def test_resumo_com_ano_zero(client, professor):
    resposta = client.get(
        f"{ROTA}/resumo", params={"mes": "0000-05"}, headers=cabecalho(professor)
    )
    assert resposta.status_code == 422


# --- avisos da issue: 1 mês, 1 semana, no dia, atraso, criação e edição ---


def test_um_mes_antes_ajusta_o_fim_do_mes():
    assert financeiro_service._um_mes_antes(date(2030, 3, 31)) == date(2030, 2, 28)
    assert financeiro_service._um_mes_antes(date(2030, 1, 15)) == date(2029, 12, 15)


def test_semanal_nao_tem_o_aviso_de_um_mes(client, professor, aluno_maior, sessao):
    plano = _criar_plano(
        client,
        professor,
        aluno_maior,
        frequencia="semanal",
        dia_vencimento=hoje().weekday(),
    )
    ultima = _cobrancas(sessao, plano["id"])[-1]
    assert set(_avisos(sessao, ultima.id)) == {
        TipoNotificacao.COBRANCA_VENCE_EM_1_SEMANA,
        TipoNotificacao.COBRANCA_VENCE_HOJE,
        TipoNotificacao.COBRANCA_VENCIDA,
        TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR,
    }


def _definir_chave_pix(sessao, professor, chave="professora@exemplo.com"):
    sessao.get(Professor, professor.id).chave_pix = chave
    sessao.commit()


def test_avulsa_avisa_o_aluno_por_email_com_a_chave_pix(
    client, professor, aluno_maior, sessao, enviador
):
    _definir_chave_pix(sessao, professor)
    _avulsa(client, professor, aluno_maior, valor_centavos=12345)
    (email,) = enviador.mensagens
    assert email["para"] == aluno_maior.email
    assert email["assunto"] == "Novo pagamento"
    assert "R$ 123,45" in email["corpo"]
    assert "Pague pelo Pix: professora@exemplo.com" in email["corpo"]


def test_editar_cobranca_avisa_o_aluno(client, professor, aluno_maior, enviador):
    cobranca = _avulsa(client, professor, aluno_maior)
    client.patch(
        f"{ROTA}/cobrancas/{cobranca['id']}",
        json={"valor_centavos": 6000},
        headers=cabecalho(professor),
    )
    assert [email["assunto"] for email in enviador.mensagens] == [
        "Novo pagamento",
        "Pagamento alterado",
    ]
    # Sem chave Pix cadastrada, o e-mail orienta a combinar com a professora.
    assert "Combine o pagamento com" in enviador.mensagens[-1]["corpo"]


def test_plano_avisa_uma_vez_e_nao_por_cobranca(
    client, professor, aluno_maior, enviador
):
    plano = _criar_plano(
        client,
        professor,
        aluno_maior,
        frequencia="semanal",
        dia_vencimento=2,
        valor_centavos=8000,
    )
    (email,) = enviador.mensagens
    assert email["assunto"] == "Novo plano de pagamento"
    assert "R$ 80,00 toda quarta" in email["corpo"]

    client.patch(
        f"{ROTA}/planos/{plano['id']}",
        json={"valor_centavos": 9000},
        headers=cabecalho(professor),
    )
    assert [email["assunto"] for email in enviador.mensagens] == [
        "Novo plano de pagamento",
        "Plano de pagamento alterado",
    ]


def test_atraso_avisa_a_professora_por_email(client, professor, aluno_maior, sessao):
    cobranca = _avulsa(
        client, professor, aluno_maior, vencimento=hoje() - timedelta(days=1)
    )
    conteudo = financeiro_service.RESOLVEDORES[
        TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR
    ](sessao, cobranca["id"])
    assert conteudo.email is True
    assert list(conteudo.usuario_ids) == [professor.id]


def test_plano_encerrado_nao_avisa(client, professor, aluno_maior, sessao):
    plano = _criar_plano(client, professor, aluno_maior)
    client.delete(f"{ROTA}/planos/{plano['id']}", headers=cabecalho(professor))
    sessao.expire_all()
    for tipo in financeiro_service.TIPOS_DO_PLANO:
        assert financeiro_service.RESOLVEDORES[tipo](sessao, plano["id"]) is None

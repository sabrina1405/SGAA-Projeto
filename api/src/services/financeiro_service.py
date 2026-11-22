"""Cobranças pagas por Pix fora do app, com baixa manual pela professora.

As recorrentes vêm de um plano por aluno, mensal ou semanal, e são geradas com
alguns dias de antecedência pela tarefa agendada. "Vencida" não é guardada: é a
pendente com o vencimento no passado, calculada na consulta.
"""

import calendar
import logging
from collections.abc import Iterator, Sequence
from datetime import date, datetime, time, timedelta

from sqlalchemy import Row, String, case, cast, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from src.core.security import agora
from src.models.financeiro import (
    Cobranca,
    FrequenciaPlano,
    PlanoCobranca,
    StatusCobranca,
)
from src.models.notificacao import TipoNotificacao
from src.models.professor import Professor
from src.models.usuario import Usuario
from src.schemas.aluno import HORARIO_DE_BRASILIA, hoje
from src.services import notificacao_service
from src.services.usuario_service import validar_alunos

logger = logging.getLogger(__name__)

# Gera com antecedência suficiente para o aviso de 1 mês antes.
HORIZONTE = timedelta(days=35)
HORA_DO_AVISO = time(9, tzinfo=HORARIO_DE_BRASILIA)

LEMBRETES = (
    TipoNotificacao.COBRANCA_VENCE_EM_1_MES,
    TipoNotificacao.COBRANCA_VENCE_EM_1_SEMANA,
    TipoNotificacao.COBRANCA_VENCE_HOJE,
)
TIPOS_DA_COBRANCA = (
    TipoNotificacao.COBRANCA_CRIADA,
    TipoNotificacao.COBRANCA_EDITADA,
    *LEMBRETES,
    TipoNotificacao.COBRANCA_VENCIDA,
    TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR,
)
TIPOS_DO_PLANO = (TipoNotificacao.PLANO_CRIADO, TipoNotificacao.PLANO_EDITADO)
DIAS_DA_SEMANA = (
    "toda segunda",
    "toda terça",
    "toda quarta",
    "toda quinta",
    "toda sexta",
    "todo sábado",
    "todo domingo",
)


class PlanoNaoEncontrado(Exception):
    pass


class CobrancaNaoEncontrada(Exception):
    pass


class TransicaoInvalida(Exception):
    """A cobrança não está no status que a operação exige."""


class VencimentoDuplicado(Exception):
    """O plano já tem uma cobrança nesse vencimento."""


# --- vencimentos ---


def _vencimento_mensal(ano: int, mes: int, dia: int) -> date:
    return date(ano, mes, min(dia, calendar.monthrange(ano, mes)[1]))


def vencimentos(plano: PlanoCobranca, desde: date, ate: date) -> Iterator[date]:
    """Datas de vencimento do plano entre `desde` e `ate`, dentro da vigência."""
    inicio = max(desde, plano.inicio)
    fim = ate if plano.fim is None else min(ate, plano.fim)
    if plano.frequencia == FrequenciaPlano.SEMANAL:
        dia = inicio + timedelta(days=(plano.dia_vencimento - inicio.weekday()) % 7)
        while dia <= fim:
            yield dia
            dia += timedelta(weeks=1)
        return
    ano, mes = inicio.year, inicio.month
    while True:
        dia = _vencimento_mensal(ano, mes, plano.dia_vencimento)
        if dia > fim:
            return
        if dia >= inicio:
            yield dia
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def _proximo_periodo(plano: PlanoCobranca, vencimento: date) -> date:
    """Início do mês ou da semana (segunda) seguinte ao vencimento: cada período
    tem uma cobrança só, mesmo que o dia de vencimento mude."""
    if plano.frequencia == FrequenciaPlano.SEMANAL:
        return vencimento + timedelta(days=7 - vencimento.weekday())
    if vencimento.month == 12:
        return date(vencimento.year + 1, 1, 1)
    return date(vencimento.year, vencimento.month + 1, 1)


# --- avisos ---


def _momento(dia: date) -> datetime:
    return datetime.combine(dia, HORA_DO_AVISO)


def _um_mes_antes(dia: date) -> date:
    ano, mes = (dia.year - 1, 12) if dia.month == 1 else (dia.year, dia.month - 1)
    return _vencimento_mensal(ano, mes, dia.day)


def _agendar_avisos(
    sessao: Session, cobranca_id: int, vencimento: date, *, semanal: bool = False
) -> None:
    """Lembretes de 1 mês (fora do semanal), 1 semana e no dia, e o de atraso no
    dia seguinte. Os lembretes que já passaram não são agendados."""
    momento = agora()
    candidatos = {
        TipoNotificacao.COBRANCA_VENCE_EM_1_SEMANA: _momento(
            vencimento - timedelta(weeks=1)
        ),
        TipoNotificacao.COBRANCA_VENCE_HOJE: _momento(vencimento),
    }
    if not semanal:
        candidatos[TipoNotificacao.COBRANCA_VENCE_EM_1_MES] = _momento(
            _um_mes_antes(vencimento)
        )
    for tipo, enviar_em in candidatos.items():
        if enviar_em > momento:
            notificacao_service.agendar(sessao, tipo, cobranca_id, enviar_em)
    # O de atraso sai mesmo se a data já passou: a cobrança está em atraso.
    vencida = max(_momento(vencimento + timedelta(days=1)), momento)
    for tipo in (
        TipoNotificacao.COBRANCA_VENCIDA,
        TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR,
    ):
        notificacao_service.agendar(sessao, tipo, cobranca_id, vencida)


def _cancelar_avisos(sessao: Session, cobranca_id: int) -> None:
    for tipo in TIPOS_DA_COBRANCA:
        notificacao_service.cancelar_pendentes(sessao, tipo, cobranca_id)


def _avisar_agora(sessao: Session, tipo: TipoNotificacao, referencia_id: int):
    """Aviso de criação ou edição. Não faz commit; o id existe depois dele."""
    return notificacao_service.agendar(sessao, tipo, referencia_id, agora())


def _semanal(sessao: Session, cobranca: Cobranca) -> bool:
    if cobranca.plano_id is None:
        return False
    plano = sessao.get(PlanoCobranca, cobranca.plano_id)
    return plano.frequencia == FrequenciaPlano.SEMANAL


def formatar_valor(centavos: int) -> str:
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def _periodicidade(plano: PlanoCobranca) -> str:
    if plano.frequencia == FrequenciaPlano.SEMANAL:
        return DIAS_DA_SEMANA[plano.dia_vencimento]
    return f"todo dia {plano.dia_vencimento}"


_TITULOS: dict[TipoNotificacao, str] = {
    TipoNotificacao.COBRANCA_CRIADA: "Novo pagamento",
    TipoNotificacao.COBRANCA_EDITADA: "Pagamento alterado",
    TipoNotificacao.COBRANCA_VENCE_EM_1_MES: "Pagamento vence em 1 mês",
    TipoNotificacao.COBRANCA_VENCE_EM_1_SEMANA: "Pagamento vence em 1 semana",
    TipoNotificacao.COBRANCA_VENCE_HOJE: "Pagamento vence hoje",
    TipoNotificacao.COBRANCA_VENCIDA: "Pagamento em atraso",
    TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR: "Pagamento em atraso",
    TipoNotificacao.PLANO_CRIADO: "Novo plano de pagamento",
    TipoNotificacao.PLANO_EDITADO: "Plano de pagamento alterado",
}

RODAPE_DO_EMAIL = "\n\nEste é um aviso automático do SGAA. Não responda este e-mail."


def _ativos(sessao: Session, professor_id: int, aluno_id: int):
    """A professora e o aluno, ou None se algum foi excluído."""
    professor = sessao.get(Usuario, professor_id)
    aluno = sessao.get(Usuario, aluno_id)
    if any(
        usuario is None or usuario.deletado_em is not None
        for usuario in (professor, aluno)
    ):
        return None
    return professor, aluno


def _email_do_aluno(sessao: Session, professor: Usuario, corpo: str) -> str:
    chave_pix = sessao.get(Professor, professor.id).chave_pix
    pagamento = (
        f"Pague pelo Pix: {chave_pix}"
        if chave_pix
        else f"Combine o pagamento com {professor.nome_completo}."
    )
    return f"{corpo}.\n\n{pagamento}{RODAPE_DO_EMAIL}"


def _resolvedor_da_cobranca(tipo: TipoNotificacao) -> notificacao_service.Resolvedor:
    def resolver(
        sessao: Session, cobranca_id: int
    ) -> notificacao_service.Conteudo | None:
        cobranca = sessao.get(Cobranca, cobranca_id)
        if (
            cobranca is None
            or cobranca.deletado_em is not None
            or cobranca.status != StatusCobranca.PENDENTE
        ):
            return None
        # Cobre uma nova tentativa que só saiu depois do vencimento.
        if tipo in LEMBRETES and cobranca.vencimento < hoje():
            return None
        pessoas = _ativos(sessao, cobranca.professor_id, cobranca.aluno_id)
        if pessoas is None:
            return None
        professor, aluno = pessoas
        valor = formatar_valor(cobranca.valor_centavos)
        data = cobranca.vencimento.strftime("%d/%m")
        dados = {"tipo": tipo.value, "cobranca_id": cobranca.id}
        if tipo == TipoNotificacao.COBRANCA_VENCIDA_PROFESSOR:
            corpo = f"{cobranca.descricao}, {valor}, venceu em {data}"
            return notificacao_service.Conteudo(
                usuario_ids=[professor.id],
                titulo=f"{_TITULOS[tipo]}: {aluno.nome_completo}",
                corpo=corpo,
                dados=dados,
                email=True,
                corpo_email=f"{corpo}.{RODAPE_DO_EMAIL}",
            )
        corpo = (
            f"{cobranca.descricao}, {valor}, vencimento em {data}, "
            f"com {professor.nome_completo}"
        )
        return notificacao_service.Conteudo(
            usuario_ids=[aluno.id],
            titulo=_TITULOS[tipo],
            corpo=corpo,
            dados=dados,
            email=True,
            corpo_email=_email_do_aluno(sessao, professor, corpo),
        )

    return resolver


def _resolvedor_do_plano(tipo: TipoNotificacao) -> notificacao_service.Resolvedor:
    def resolver(sessao: Session, plano_id: int) -> notificacao_service.Conteudo | None:
        plano = sessao.get(PlanoCobranca, plano_id)
        if plano is None or plano.deletado_em is not None:
            return None
        pessoas = _ativos(sessao, plano.professor_id, plano.aluno_id)
        if pessoas is None:
            return None
        professor, aluno = pessoas
        corpo = (
            f"{plano.descricao}, {formatar_valor(plano.valor_centavos)} "
            f"{_periodicidade(plano)}, com {professor.nome_completo}"
        )
        return notificacao_service.Conteudo(
            usuario_ids=[aluno.id],
            titulo=_TITULOS[tipo],
            corpo=corpo,
            dados={"tipo": tipo.value, "plano_id": plano.id},
            email=True,
            corpo_email=_email_do_aluno(sessao, professor, corpo),
        )

    return resolver


RESOLVEDORES: dict[TipoNotificacao, notificacao_service.Resolvedor] = {
    **{tipo: _resolvedor_da_cobranca(tipo) for tipo in TIPOS_DA_COBRANCA},
    **{tipo: _resolvedor_do_plano(tipo) for tipo in TIPOS_DO_PLANO},
}


# --- geração das recorrentes ---


def _gerar_do_plano(sessao: Session, plano: PlanoCobranca, ate: date) -> int:
    """Não faz commit. Devolve quantas cobranças criou.

    Nunca gera vencimentos antes de hoje: depois de editar o plano, o último
    vencimento pode ser antigo, e a regra nova só vale daqui para a frente.
    """
    ultimo = sessao.scalar(
        select(func.max(Cobranca.vencimento)).where(Cobranca.plano_id == plano.id)
    )
    desde = plano.inicio if ultimo is None else _proximo_periodo(plano, ultimo)
    desde = max(desde, hoje())
    datas = list(vencimentos(plano, desde, ate))
    if not datas:
        return 0
    criadas = sessao.execute(
        insert(Cobranca)
        .values(
            [
                {
                    "professor_id": plano.professor_id,
                    "aluno_id": plano.aluno_id,
                    "plano_id": plano.id,
                    "descricao": plano.descricao,
                    "valor_centavos": plano.valor_centavos,
                    "vencimento": data,
                }
                for data in datas
            ]
        )
        # Outra execução simultânea pode ter gerado a mesma data.
        .on_conflict_do_nothing(constraint="uq_cobranca_plano_vencimento")
        .returning(Cobranca.id, Cobranca.vencimento)
    ).all()
    for cobranca_id, vencimento in criadas:
        _agendar_avisos(
            sessao,
            cobranca_id,
            vencimento,
            semanal=plano.frequencia == FrequenciaPlano.SEMANAL,
        )
    return len(criadas)


def gerar_cobrancas(sessao: Session, data: date | None = None) -> int:
    """Gera as cobranças dos planos ativos que vencem até `data` + HORIZONTE."""
    ate = (data or hoje()) + HORIZONTE
    planos = sessao.scalars(
        select(PlanoCobranca)
        .join(Usuario, Usuario.id == PlanoCobranca.aluno_id)
        .where(
            PlanoCobranca.deletado_em.is_(None),
            Usuario.deletado_em.is_(None),
            PlanoCobranca.inicio <= ate,
        )
        .order_by(PlanoCobranca.id)
    ).all()
    total = 0
    for plano in planos:
        total += _gerar_do_plano(sessao, plano, ate)
        sessao.commit()
    return total


def gerar_cobrancas_sem_falhar(sessao: Session) -> int:
    """Para a tarefa agendada: um erro aqui não afeta o envio da fila."""
    try:
        return gerar_cobrancas(sessao)
    except Exception:
        logger.exception("Falha ao gerar as cobranças recorrentes")
        sessao.rollback()
        return 0


# --- planos ---


def _plano_do_professor(
    sessao: Session, professor: Usuario, plano_id: int
) -> PlanoCobranca:
    plano = sessao.get(PlanoCobranca, plano_id)
    if (
        plano is None
        or plano.deletado_em is not None
        or plano.professor_id != professor.id
    ):
        raise PlanoNaoEncontrado
    return plano


def criar_plano(
    sessao: Session,
    professor: Usuario,
    *,
    aluno_id: int,
    descricao: str,
    valor_centavos: int,
    frequencia: FrequenciaPlano,
    dia_vencimento: int,
    inicio: date,
    fim: date | None = None,
) -> tuple[PlanoCobranca, int]:
    """Já gera as cobranças que vencem nos próximos dias. Devolve o plano e o id
    do aviso ao aluno, que sai na hora.

    Levanta AlunosInvalidos, sem criar o plano.
    """
    validar_alunos(sessao, [aluno_id])
    plano = PlanoCobranca(
        professor_id=professor.id,
        aluno_id=aluno_id,
        descricao=descricao,
        valor_centavos=valor_centavos,
        frequencia=frequencia,
        dia_vencimento=dia_vencimento,
        inicio=inicio,
        fim=fim,
    )
    sessao.add(plano)
    sessao.flush()
    _gerar_do_plano(sessao, plano, hoje() + HORIZONTE)
    aviso = _avisar_agora(sessao, TipoNotificacao.PLANO_CRIADO, plano.id)
    sessao.commit()
    return plano, aviso.id


_ALUNO = aliased(Usuario)


def _consulta_planos():
    return select(
        PlanoCobranca.id,
        PlanoCobranca.aluno_id,
        _ALUNO.nome_completo.label("aluno_nome"),
        PlanoCobranca.descricao,
        PlanoCobranca.valor_centavos,
        PlanoCobranca.frequencia,
        PlanoCobranca.dia_vencimento,
        PlanoCobranca.inicio,
        PlanoCobranca.fim,
        PlanoCobranca.criado_em,
    ).join(_ALUNO, _ALUNO.id == PlanoCobranca.aluno_id)


def listar_planos(
    sessao: Session,
    professor: Usuario,
    *,
    aluno_id: int | None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    filtros = [
        PlanoCobranca.professor_id == professor.id,
        PlanoCobranca.deletado_em.is_(None),
    ]
    if aluno_id is not None:
        filtros.append(PlanoCobranca.aluno_id == aluno_id)
    total = sessao.scalar(
        select(func.count()).select_from(PlanoCobranca).where(*filtros)
    )
    itens = sessao.execute(
        _consulta_planos()
        .where(*filtros)
        .order_by(func.lower(func.unaccent(_ALUNO.nome_completo)), PlanoCobranca.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def dados_plano(sessao: Session, plano: PlanoCobranca) -> Row:
    return sessao.execute(_consulta_planos().where(PlanoCobranca.id == plano.id)).one()


def obter_plano(sessao: Session, professor: Usuario, plano_id: int) -> PlanoCobranca:
    """Levanta PlanoNaoEncontrado."""
    return _plano_do_professor(sessao, professor, plano_id)


def _futuras_pendentes(plano: PlanoCobranca):
    """Cobranças do plano que ainda não venceram nem foram pagas."""
    return (
        Cobranca.plano_id == plano.id,
        Cobranca.status == StatusCobranca.PENDENTE,
        Cobranca.deletado_em.is_(None),
        Cobranca.vencimento >= hoje(),
    )


def _descartar_futuras(sessao: Session, plano: PlanoCobranca) -> None:
    """Apaga as projeções ainda não vencidas, para gerar de novo com a regra nova."""
    ids = sessao.scalars(select(Cobranca.id).where(*_futuras_pendentes(plano))).all()
    for cobranca_id in ids:
        _cancelar_avisos(sessao, cobranca_id)
    if ids:
        sessao.execute(delete(Cobranca).where(Cobranca.id.in_(ids)))


def atualizar_plano(
    sessao: Session, professor: Usuario, plano_id: int, campos: dict
) -> tuple[PlanoCobranca, int]:
    """Altera os campos presentes em `campos`. As cobranças ainda não vencidas
    seguem a mudança; as vencidas e as pagas ficam como estão. Devolve o plano e
    o id do aviso ao aluno, que sai na hora.

    Levanta PlanoNaoEncontrado e ValueError (dia ou fim incompatíveis).
    """
    plano = _plano_do_professor(sessao, professor, plano_id)
    dia = campos.get("dia_vencimento", plano.dia_vencimento)
    limites = (1, 31) if plano.frequencia == FrequenciaPlano.MENSAL else (0, 6)
    if not limites[0] <= dia <= limites[1]:
        raise ValueError(
            f"no plano {plano.frequencia.value}, o dia de vencimento vai de "
            f"{limites[0]} a {limites[1]}"
        )
    fim = campos.get("fim", plano.fim)
    if fim is not None and fim < plano.inicio:
        raise ValueError("o fim não pode ser anterior ao início")

    for campo, valor in campos.items():
        setattr(plano, campo, valor)
    if "dia_vencimento" in campos or "fim" in campos:
        # As datas mudam: as projeções futuras são refeitas.
        _descartar_futuras(sessao, plano)
    else:
        sessao.execute(
            update(Cobranca)
            .where(*_futuras_pendentes(plano))
            .values(descricao=plano.descricao, valor_centavos=plano.valor_centavos)
        )
    sessao.flush()
    _gerar_do_plano(sessao, plano, hoje() + HORIZONTE)
    # Um aviso pelo plano, e não um por cobrança alterada.
    aviso = _avisar_agora(sessao, TipoNotificacao.PLANO_EDITADO, plano.id)
    sessao.commit()
    return plano, aviso.id


def encerrar_plano(sessao: Session, professor: Usuario, plano_id: int) -> None:
    """As cobranças ainda não vencidas são canceladas; as vencidas seguem devidas.

    Levanta PlanoNaoEncontrado.
    """
    plano = _plano_do_professor(sessao, professor, plano_id)
    ids = sessao.scalars(select(Cobranca.id).where(*_futuras_pendentes(plano))).all()
    for cobranca_id in ids:
        _cancelar_avisos(sessao, cobranca_id)
    if ids:
        sessao.execute(
            update(Cobranca)
            .where(Cobranca.id.in_(ids))
            .values(status=StatusCobranca.CANCELADA)
        )
    plano.deletado_em = agora()
    sessao.commit()


# --- cobranças da professora ---


def situacao(data: date | None = None):
    """Expressão SQL da situação: o status, com a pendente atrasada como vencida."""
    return case(
        (
            (Cobranca.status == StatusCobranca.PENDENTE)
            & (Cobranca.vencimento < (data or hoje())),
            "vencida",
        ),
        else_=cast(Cobranca.status, String),
    ).label("situacao")


def _filtro_situacao(valor: str):
    data = hoje()
    pendente = Cobranca.status == StatusCobranca.PENDENTE
    return {
        "pendente": pendente & (Cobranca.vencimento >= data),
        "vencida": pendente & (Cobranca.vencimento < data),
        "paga": Cobranca.status == StatusCobranca.PAGA,
        "cancelada": Cobranca.status == StatusCobranca.CANCELADA,
    }[valor]


def _cobranca_do_professor(
    sessao: Session, professor: Usuario, cobranca_id: int
) -> Cobranca:
    cobranca = sessao.get(Cobranca, cobranca_id, with_for_update=True)
    if (
        cobranca is None
        or cobranca.deletado_em is not None
        or cobranca.professor_id != professor.id
    ):
        raise CobrancaNaoEncontrada
    return cobranca


def _consulta_cobrancas():
    return select(
        Cobranca.id,
        Cobranca.aluno_id,
        _ALUNO.nome_completo.label("aluno_nome"),
        Cobranca.plano_id,
        Cobranca.descricao,
        Cobranca.valor_centavos,
        Cobranca.vencimento,
        situacao(),
        Cobranca.paga_em,
        Cobranca.criado_em,
    ).join(_ALUNO, _ALUNO.id == Cobranca.aluno_id)


def criar_cobranca(
    sessao: Session,
    professor: Usuario,
    *,
    aluno_id: int,
    descricao: str,
    valor_centavos: int,
    vencimento: date,
) -> tuple[Cobranca, int]:
    """Cobrança avulsa. Devolve a cobrança e o id do aviso ao aluno, que sai na
    hora. Levanta AlunosInvalidos, sem criar nada."""
    validar_alunos(sessao, [aluno_id])
    cobranca = Cobranca(
        professor_id=professor.id,
        aluno_id=aluno_id,
        descricao=descricao,
        valor_centavos=valor_centavos,
        vencimento=vencimento,
    )
    sessao.add(cobranca)
    sessao.flush()
    _agendar_avisos(sessao, cobranca.id, vencimento)
    aviso = _avisar_agora(sessao, TipoNotificacao.COBRANCA_CRIADA, cobranca.id)
    sessao.commit()
    return cobranca, aviso.id


def listar_cobrancas(
    sessao: Session,
    professor: Usuario,
    *,
    aluno_id: int | None = None,
    situacao_filtro: str | None = None,
    de: date | None = None,
    ate: date | None = None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    """Por vencimento, do mais antigo ao mais novo, e o total sem paginar."""
    filtros = [Cobranca.professor_id == professor.id, Cobranca.deletado_em.is_(None)]
    if aluno_id is not None:
        filtros.append(Cobranca.aluno_id == aluno_id)
    if situacao_filtro is not None:
        filtros.append(_filtro_situacao(situacao_filtro))
    if de is not None:
        filtros.append(Cobranca.vencimento >= de)
    if ate is not None:
        filtros.append(Cobranca.vencimento <= ate)
    total = sessao.scalar(select(func.count()).select_from(Cobranca).where(*filtros))
    itens = sessao.execute(
        _consulta_cobrancas()
        .where(*filtros)
        .order_by(Cobranca.vencimento, Cobranca.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def dados_cobranca(sessao: Session, cobranca: Cobranca) -> Row:
    return sessao.execute(_consulta_cobrancas().where(Cobranca.id == cobranca.id)).one()


def obter_cobranca(sessao: Session, professor: Usuario, cobranca_id: int) -> Cobranca:
    """Levanta CobrancaNaoEncontrada."""
    return _cobranca_do_professor(sessao, professor, cobranca_id)


def atualizar_cobranca(
    sessao: Session, professor: Usuario, cobranca_id: int, campos: dict
) -> tuple[Cobranca, int]:
    """Só para pendentes. Devolve a cobrança e o id do aviso ao aluno, que sai
    na hora.

    Levanta CobrancaNaoEncontrada, TransicaoInvalida e VencimentoDuplicado, sem
    alterar nada."""
    cobranca = _cobranca_do_professor(sessao, professor, cobranca_id)
    if cobranca.status != StatusCobranca.PENDENTE:
        raise TransicaoInvalida
    for campo, valor in campos.items():
        setattr(cobranca, campo, valor)
    try:
        sessao.flush()
    except IntegrityError:
        sessao.rollback()
        raise VencimentoDuplicado from None
    if "vencimento" in campos:
        _cancelar_avisos(sessao, cobranca.id)
        _agendar_avisos(
            sessao,
            cobranca.id,
            cobranca.vencimento,
            semanal=_semanal(sessao, cobranca),
        )
    aviso = _avisar_agora(sessao, TipoNotificacao.COBRANCA_EDITADA, cobranca.id)
    sessao.commit()
    return cobranca, aviso.id


def pagar(
    sessao: Session,
    professor: Usuario,
    cobranca_id: int,
    paga_em: datetime | None = None,
) -> Cobranca:
    """Levanta CobrancaNaoEncontrada e TransicaoInvalida."""
    cobranca = _cobranca_do_professor(sessao, professor, cobranca_id)
    if cobranca.status != StatusCobranca.PENDENTE:
        raise TransicaoInvalida
    cobranca.status = StatusCobranca.PAGA
    cobranca.paga_em = paga_em or agora()
    _cancelar_avisos(sessao, cobranca.id)
    sessao.commit()
    return cobranca


def reabrir(sessao: Session, professor: Usuario, cobranca_id: int) -> Cobranca:
    """Desfaz a baixa. Levanta CobrancaNaoEncontrada e TransicaoInvalida."""
    cobranca = _cobranca_do_professor(sessao, professor, cobranca_id)
    if cobranca.status != StatusCobranca.PAGA:
        raise TransicaoInvalida
    cobranca.status = StatusCobranca.PENDENTE
    cobranca.paga_em = None
    _agendar_avisos(
        sessao, cobranca.id, cobranca.vencimento, semanal=_semanal(sessao, cobranca)
    )
    sessao.commit()
    return cobranca


def cancelar(sessao: Session, professor: Usuario, cobranca_id: int) -> Cobranca:
    """Levanta CobrancaNaoEncontrada e TransicaoInvalida."""
    cobranca = _cobranca_do_professor(sessao, professor, cobranca_id)
    if cobranca.status != StatusCobranca.PENDENTE:
        raise TransicaoInvalida
    cobranca.status = StatusCobranca.CANCELADA
    _cancelar_avisos(sessao, cobranca.id)
    sessao.commit()
    return cobranca


def resumo_do_mes(sessao: Session, professor: Usuario, ano: int, mes: int) -> dict:
    """Totais em centavos das cobranças que vencem no mês, sem as canceladas."""
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
    data = hoje()
    pendente = Cobranca.status == StatusCobranca.PENDENTE

    def soma(condicao):
        return func.coalesce(
            func.sum(case((condicao, Cobranca.valor_centavos), else_=0)), 0
        )

    linha = sessao.execute(
        select(
            soma(Cobranca.status == StatusCobranca.PAGA).label("recebido"),
            soma(pendente & (Cobranca.vencimento >= data)).label("pendente"),
            soma(pendente & (Cobranca.vencimento < data)).label("vencido"),
        ).where(
            Cobranca.professor_id == professor.id,
            Cobranca.deletado_em.is_(None),
            Cobranca.vencimento.between(primeiro, ultimo),
        )
    ).one()
    return {
        "recebido_centavos": linha.recebido,
        "pendente_centavos": linha.pendente,
        "vencido_centavos": linha.vencido,
    }


def cobrancas_do_aluno(
    sessao: Session, professor: Usuario, aluno_id: int
) -> Sequence[Row]:
    """Para o detalhe do aluno: só as cobranças com a professora que consulta."""
    return sessao.execute(
        _consulta_cobrancas()
        .where(
            Cobranca.professor_id == professor.id,
            Cobranca.aluno_id == aluno_id,
            Cobranca.deletado_em.is_(None),
        )
        .order_by(Cobranca.vencimento.desc(), Cobranca.id.desc())
    ).all()


# --- cobranças do aluno ---

_PROFESSORA = aliased(Usuario)


def _consulta_do_aluno(aluno: Usuario):
    return (
        select(
            Cobranca.id,
            Cobranca.descricao,
            Cobranca.valor_centavos,
            Cobranca.vencimento,
            situacao(),
            Cobranca.paga_em,
            _PROFESSORA.nome_completo.label("professor_nome"),
            Professor.chave_pix,
        )
        .join(_PROFESSORA, _PROFESSORA.id == Cobranca.professor_id)
        .join(Professor, Professor.usuario_id == Cobranca.professor_id)
        .where(
            Cobranca.aluno_id == aluno.id,
            Cobranca.deletado_em.is_(None),
            _PROFESSORA.deletado_em.is_(None),
        )
    )


def listar_minhas_cobrancas(
    sessao: Session,
    aluno: Usuario,
    *,
    situacao_filtro: str | None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    """Da mais recente à mais antiga, de todas as professoras, e o total."""
    consulta = _consulta_do_aluno(aluno)
    if situacao_filtro is not None:
        consulta = consulta.where(_filtro_situacao(situacao_filtro))
    total = sessao.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = sessao.execute(
        consulta.order_by(Cobranca.vencimento.desc(), Cobranca.id.desc())
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_minha_cobranca(sessao: Session, aluno: Usuario, cobranca_id: int) -> Row:
    """Levanta CobrancaNaoEncontrada também para a cobrança de outro aluno."""
    linha = sessao.execute(
        _consulta_do_aluno(aluno).where(Cobranca.id == cobranca_id)
    ).first()
    if linha is None:
        raise CobrancaNaoEncontrada
    return linha

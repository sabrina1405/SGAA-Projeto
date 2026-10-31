"""Agenda de aulas: o professor monta e altera, o aluno consulta e cancela a
própria participação, o que deixa uma reposição pendente para o professor."""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

from sqlalchemy import Row, Select, and_, case, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.security import agora
from src.models.aula import Aula, AulaAluno, AulaGrupo, StatusAula, StatusParticipacao
from src.models.grupo import Grupo, GrupoAluno
from src.models.notificacao import TipoNotificacao
from src.models.professor import Professor
from src.models.usuario import Usuario
from src.schemas.aluno import HORARIO_DE_BRASILIA
from src.schemas.aula import Escopo
from src.services import notificacao_service
from src.services.grupo_service import validar_grupos
from src.services.usuario_service import (
    ORDEM_DOS_ALUNOS,
    consulta_alunos,
    validar_alunos,
)

DURACAO_MAXIMA = timedelta(hours=12)
SEMANAS_DE_REPETICAO = 26
# Cobre a visão mensal, que mostra semanas do mês anterior e do seguinte.
DIAS_DA_LISTAGEM = 62
SEMANA = timedelta(weeks=1)

LEMBRETES = {
    TipoNotificacao.AULA_LEMBRETE_SEMANA: (timedelta(weeks=1), "Aula em 1 semana"),
    TipoNotificacao.AULA_LEMBRETE_DIA: (timedelta(days=1), "Aula amanhã"),
    TipoNotificacao.AULA_LEMBRETE_30MIN: (timedelta(minutes=30), "Aula em 30 minutos"),
}
DIAS_DA_SEMANA = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")


class AulaNaoEncontrada(Exception):
    pass


class AlunoForaDaAula(Exception):
    pass


class ReposicaoNaoEncontrada(Exception):
    pass


class AulaInvalida(Exception):
    """Regra que depende da aula inteira, e não de um campo só."""

    def __init__(self, tipo: str, mensagem: str, campos: list[str]) -> None:
        super().__init__(mensagem)
        self.tipo = tipo
        self.mensagem = mensagem
        self.campos = campos


class ConflitoDeHorario(Exception):
    def __init__(self, aula: Aula) -> None:
        super().__init__(aula.id)
        self.aula = aula


class OperacaoNaoPermitida(Exception):
    """O status da aula não permite a ação."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


def formatar_horario(momento: datetime) -> str:
    """Ex.: "qui, 24/09 às 15:00", no horário de Brasília."""
    local = momento.astimezone(HORARIO_DE_BRASILIA)
    return f"{DIAS_DA_SEMANA[local.weekday()]}, {local:%d/%m} às {local:%H:%M}"


def _periodo(data_inicio: date, data_fim: date) -> tuple[datetime, datetime]:
    """Levanta AulaInvalida. Devolve o intervalo [de, até) no horário de Brasília."""
    if data_fim < data_inicio:
        raise AulaInvalida(
            "periodo_invalido",
            "a data de fim não pode ser anterior à data de início",
            ["data_fim"],
        )
    if (data_fim - data_inicio).days >= DIAS_DA_LISTAGEM:
        raise AulaInvalida(
            "periodo_invalido",
            f"o período pode ter no máximo {DIAS_DA_LISTAGEM} dias",
            ["data_fim"],
        )
    meia_noite = time(tzinfo=HORARIO_DE_BRASILIA)
    return (
        datetime.combine(data_inicio, meia_noite),
        datetime.combine(data_fim + timedelta(days=1), meia_noite),
    )


# --- regras da agenda do professor ---


def _aula_do_professor(sessao: Session, professor: Usuario, aula_id: int) -> Aula:
    aula = sessao.get(Aula, aula_id)
    if (
        aula is None
        or aula.deletado_em is not None
        or aula.professor_id != professor.id
    ):
        raise AulaNaoEncontrada
    return aula


def _exigir_agendada(aula: Aula, mensagem: str) -> None:
    if aula.status != StatusAula.AGENDADA:
        raise OperacaoNaoPermitida(mensagem)


def _conferir_horario(inicio: datetime, fim: datetime) -> None:
    if fim <= inicio:
        raise AulaInvalida(
            "horario_invalido", "o fim da aula deve ser depois do início", ["fim"]
        )
    if fim - inicio > DURACAO_MAXIMA:
        raise AulaInvalida(
            "horario_invalido", "a aula pode durar no máximo 12 horas", ["fim"]
        )
    if inicio <= agora():
        raise AulaInvalida(
            "horario_invalido", "a aula precisa começar no futuro", ["inicio"]
        )


def _ocorrencias(
    inicio: datetime,
    fim: datetime,
    repetir_semanalmente: bool,
    repetir_ate: date | None,
) -> list[tuple[datetime, datetime]]:
    """Levanta AulaInvalida. Devolve o horário de cada aula a criar."""
    if not repetir_semanalmente:
        if repetir_ate is not None:
            raise AulaInvalida(
                "repeticao_invalida",
                "repetir_ate só vale com repetir_semanalmente",
                ["repetir_ate"],
            )
        return [(inicio, fim)]
    primeiro_dia = inicio.astimezone(HORARIO_DE_BRASILIA).date()
    if repetir_ate is None or repetir_ate < primeiro_dia:
        raise AulaInvalida(
            "repeticao_invalida",
            "informe em repetir_ate uma data a partir do dia da primeira aula",
            ["repetir_ate"],
        )
    if repetir_ate > primeiro_dia + timedelta(weeks=SEMANAS_DE_REPETICAO):
        raise AulaInvalida(
            "repeticao_invalida",
            f"a repetição pode durar no máximo {SEMANAS_DE_REPETICAO} semanas",
            ["repetir_ate"],
        )
    horarios = []
    while inicio.astimezone(HORARIO_DE_BRASILIA).date() <= repetir_ate:
        horarios.append((inicio, fim))
        inicio, fim = inicio + SEMANA, fim + SEMANA
    return horarios


def _travar_agenda(sessao: Session, professor_id: int) -> None:
    """Enfileira as alterações de horário do professor, para que duas chamadas
    simultâneas não marquem aulas sobrepostas."""
    sessao.execute(
        select(Professor.usuario_id)
        .where(Professor.usuario_id == professor_id)
        .with_for_update()
    )


def _conferir_conflitos(
    sessao: Session,
    professor_id: int,
    horarios: Sequence[tuple[datetime, datetime]],
    ignorar: Sequence[int] = (),
) -> None:
    """Levanta ConflitoDeHorario com a primeira aula ativa sobreposta."""
    _travar_agenda(sessao, professor_id)
    conflito = sessao.scalar(
        select(Aula)
        .where(
            Aula.professor_id == professor_id,
            Aula.deletado_em.is_(None),
            Aula.status != StatusAula.CANCELADA,
            Aula.id.not_in(ignorar),
            or_(
                *(
                    and_(Aula.inicio < fim, Aula.fim > inicio)
                    for inicio, fim in horarios
                )
            ),
        )
        .order_by(Aula.inicio, Aula.id)
        .limit(1)
    )
    if conflito is not None:
        raise ConflitoDeHorario(conflito)


def _participantes(
    sessao: Session,
    professor: Usuario,
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> list[int]:
    """Os alunos informados mais os dos grupos, sem repetição.

    Levanta AlunosInvalidos e GruposInvalidos.
    """
    validar_alunos(sessao, aluno_ids)
    validar_grupos(sessao, professor, grupo_ids)
    dos_grupos: Sequence[int] = ()
    if grupo_ids:
        dos_grupos = sessao.scalars(
            consulta_alunos()
            .with_only_columns(Usuario.id)
            .join(GrupoAluno, GrupoAluno.aluno_id == Usuario.id)
            .where(GrupoAluno.grupo_id.in_(grupo_ids))
            .order_by(Usuario.id)
        ).all()
    return list(dict.fromkeys([*aluno_ids, *dos_grupos]))


def _vincular(
    sessao: Session,
    aula_ids: Sequence[int],
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> None:
    """Quem já está na aula é ignorado, mantendo a participação como estava."""
    if aluno_ids:
        sessao.execute(
            insert(AulaAluno)
            .values(
                [
                    {"aula_id": aula_id, "aluno_id": aluno_id}
                    for aula_id in aula_ids
                    for aluno_id in aluno_ids
                ]
            )
            .on_conflict_do_nothing()
        )
    if grupo_ids:
        sessao.execute(
            insert(AulaGrupo)
            .values(
                [
                    {"aula_id": aula_id, "grupo_id": grupo_id}
                    for aula_id in aula_ids
                    for grupo_id in grupo_ids
                ]
            )
            .on_conflict_do_nothing()
        )


def _agendar_lembretes(sessao: Session, aula: Aula) -> None:
    """Só os que ainda estão por vir: uma aula daqui a 2 dias não tem o de 1 semana."""
    momento = agora()
    for tipo, (antecedencia, _) in LEMBRETES.items():
        enviar_em = aula.inicio - antecedencia
        if enviar_em > momento:
            notificacao_service.agendar(sessao, tipo, aula.id, enviar_em)


def _descartar_lembretes(sessao: Session, aula: Aula) -> None:
    for tipo in LEMBRETES:
        notificacao_service.cancelar_pendentes(sessao, tipo, aula.id)


def _no_escopo(sessao: Session, aula: Aula, escopo: Escopo) -> list[Aula]:
    """A aula e, em `esta_e_seguintes`, as próximas aulas agendadas da série."""
    if escopo == Escopo.ESTA or aula.serie_id is None:
        return [aula]
    seguintes = sessao.scalars(
        select(Aula)
        .where(
            Aula.serie_id == aula.serie_id,
            Aula.inicio > aula.inicio,
            Aula.deletado_em.is_(None),
            Aula.status == StatusAula.AGENDADA,
        )
        .order_by(Aula.inicio, Aula.id)
    ).all()
    return [aula, *seguintes]


# --- aulas do professor ---


def criar_aula(
    sessao: Session,
    professor: Usuario,
    *,
    titulo: str,
    inicio: datetime,
    fim: datetime,
    descricao: str | None = None,
    anotacoes: str | None = None,
    aluno_ids: Sequence[int] = (),
    grupo_ids: Sequence[int] = (),
    repetir_semanalmente: bool = False,
    repetir_ate: date | None = None,
    reposicao_de_aula_id: int | None = None,
) -> Aula:
    """Cria a aula, ou todas as da série, e devolve a primeira.

    Levanta AulaInvalida, AlunosInvalidos, GruposInvalidos e ConflitoDeHorario,
    sem criar nada.
    """
    _conferir_horario(inicio, fim)
    horarios = _ocorrencias(inicio, fim, repetir_semanalmente, repetir_ate)
    if reposicao_de_aula_id is not None:
        try:
            _aula_do_professor(sessao, professor, reposicao_de_aula_id)
        except AulaNaoEncontrada:
            raise AulaInvalida(
                "aula_invalida",
                "a aula a repor não foi encontrada",
                ["reposicao_de_aula_id"],
            ) from None
    participantes = _participantes(sessao, professor, aluno_ids, grupo_ids)
    if not participantes:
        raise AulaInvalida(
            "sem_aluno",
            "informe ao menos um aluno ou um grupo com alunos",
            ["aluno_ids", "grupo_ids"],
        )
    _conferir_conflitos(sessao, professor.id, horarios)

    aulas = [
        Aula(
            professor_id=professor.id,
            titulo=titulo,
            descricao=descricao,
            anotacoes=anotacoes,
            inicio=inicio_da_aula,
            fim=fim_da_aula,
        )
        for inicio_da_aula, fim_da_aula in horarios
    ]
    aulas[0].reposicao_de_aula_id = reposicao_de_aula_id
    sessao.add_all(aulas)
    sessao.flush()
    if repetir_semanalmente:
        for aula in aulas:
            aula.serie_id = aulas[0].id
    _vincular(sessao, [aula.id for aula in aulas], participantes, grupo_ids)
    for aula in aulas:
        _agendar_lembretes(sessao, aula)
    if reposicao_de_aula_id is not None:
        # Resolve a pendência dos alunos que estão na reposição.
        sessao.execute(
            update(AulaAluno)
            .where(
                AulaAluno.aula_id == reposicao_de_aula_id,
                AulaAluno.aluno_id.in_(participantes),
                AulaAluno.repor,
                AulaAluno.reposta_em_aula_id.is_(None),
            )
            .values(reposta_em_aula_id=aulas[0].id)
        )
    sessao.commit()
    return aulas[0]


def listar_aulas(
    sessao: Session,
    professor: Usuario,
    *,
    data_inicio: date,
    data_fim: date,
    status: StatusAula | None = None,
    aluno_id: int | None = None,
    grupo_id: int | None = None,
) -> Sequence[Aula]:
    """Aulas que começam no período, em ordem de início. Levanta AulaInvalida."""
    de, ate = _periodo(data_inicio, data_fim)
    consulta = select(Aula).where(
        Aula.professor_id == professor.id,
        Aula.deletado_em.is_(None),
        Aula.inicio >= de,
        Aula.inicio < ate,
    )
    if status is not None:
        consulta = consulta.where(Aula.status == status)
    if aluno_id is not None:
        consulta = consulta.where(
            select(AulaAluno.aula_id)
            .where(AulaAluno.aula_id == Aula.id, AulaAluno.aluno_id == aluno_id)
            .exists()
        )
    if grupo_id is not None:
        consulta = consulta.where(
            select(AulaGrupo.aula_id)
            .where(AulaGrupo.aula_id == Aula.id, AulaGrupo.grupo_id == grupo_id)
            .exists()
        )
    return sessao.scalars(consulta.order_by(Aula.inicio, Aula.id)).all()


def alunos_das_aulas(sessao: Session, aula_ids: Sequence[int]) -> dict[int, list[Row]]:
    """Alunos de cada aula, em ordem alfabética, numa consulta só."""
    if not aula_ids:
        return {}
    linhas = sessao.execute(
        select(
            AulaAluno.aula_id,
            Usuario.id,
            Usuario.nome_completo,
            AulaAluno.status,
        )
        .join(Usuario, Usuario.id == AulaAluno.aluno_id)
        .where(AulaAluno.aula_id.in_(aula_ids), Usuario.deletado_em.is_(None))
        .order_by(*ORDEM_DOS_ALUNOS)
    ).all()
    por_aula: dict[int, list[Row]] = defaultdict(list)
    for linha in linhas:
        por_aula[linha.aula_id].append(linha)
    return por_aula


def obter_aula(sessao: Session, professor: Usuario, aula_id: int) -> Aula:
    """Levanta AulaNaoEncontrada."""
    return _aula_do_professor(sessao, professor, aula_id)


def listar_alunos_da_aula(sessao: Session, aula: Aula) -> Sequence[Row]:
    return sessao.execute(
        consulta_alunos()
        .add_columns(AulaAluno.status, AulaAluno.motivo_cancelamento, AulaAluno.repor)
        .join(AulaAluno, AulaAluno.aluno_id == Usuario.id)
        .where(AulaAluno.aula_id == aula.id)
        .order_by(*ORDEM_DOS_ALUNOS)
    ).all()


def listar_grupos_da_aula(sessao: Session, aula: Aula) -> Sequence[Row]:
    return sessao.execute(
        select(Grupo.id, Grupo.titulo)
        .join(AulaGrupo, AulaGrupo.grupo_id == Grupo.id)
        .where(AulaGrupo.aula_id == aula.id, Grupo.deletado_em.is_(None))
        .order_by(func.lower(func.unaccent(Grupo.titulo)), Grupo.id)
    ).all()


def atualizar_aula(
    sessao: Session, professor: Usuario, aula_id: int, campos: dict, escopo: Escopo
) -> Aula:
    """Altera os campos presentes em `campos` na aula e, conforme o escopo, nas
    seguintes da série. Uma mudança de horário desloca as seguintes pelo mesmo
    tanto.

    Levanta AulaNaoEncontrada, OperacaoNaoPermitida, AulaInvalida e
    ConflitoDeHorario, sem alterar nada.
    """
    aula = _aula_do_professor(sessao, professor, aula_id)
    if aula.status == StatusAula.CANCELADA:
        raise OperacaoNaoPermitida("Aula cancelada não pode ser alterada")
    status = campos.pop("status", None)
    if status is not None:
        if escopo == Escopo.ESTA_E_SEGUINTES:
            raise AulaInvalida(
                "escopo_invalido",
                "o status é alterado uma aula por vez",
                ["status"],
            )
        if status == StatusAula.REALIZADA and aula.inicio > agora():
            raise AulaInvalida(
                "status_invalido",
                "a aula só pode ser marcada como realizada depois de começar",
                ["status"],
            )

    aulas = _no_escopo(sessao, aula, escopo)
    muda_horario = "inicio" in campos or "fim" in campos
    if muda_horario:
        _exigir_agendada(aula, "Só uma aula agendada pode mudar de horário")
        deslocamento_inicio = campos.pop("inicio", aula.inicio) - aula.inicio
        deslocamento_fim = campos.pop("fim", aula.fim) - aula.fim
        horarios = [
            (item.inicio + deslocamento_inicio, item.fim + deslocamento_fim)
            for item in aulas
        ]
        for inicio, fim in horarios:
            _conferir_horario(inicio, fim)
        _conferir_conflitos(
            sessao, professor.id, horarios, ignorar=[item.id for item in aulas]
        )

    for item in aulas:
        for campo, valor in campos.items():
            setattr(item, campo, valor)
        if muda_horario:
            item.inicio += deslocamento_inicio
            item.fim += deslocamento_fim
            _descartar_lembretes(sessao, item)
            _agendar_lembretes(sessao, item)
    if status is not None:
        aula.status = status
    sessao.commit()
    return aula


def cancelar_aula(
    sessao: Session,
    professor: Usuario,
    aula_id: int,
    escopo: Escopo,
    *,
    motivo: str | None = None,
    repor: bool = False,
) -> tuple[Aula, int | None]:
    """Cancela a aula e, conforme o escopo, as seguintes da série. Os alunos
    recebem um aviso só, mesmo quando várias aulas são canceladas.

    Devolve a aula e o id da notificação do aviso, que é None se a aula já começou.

    Levanta AulaNaoEncontrada e OperacaoNaoPermitida.
    """
    aula = _aula_do_professor(sessao, professor, aula_id)
    _exigir_agendada(aula, "Só uma aula agendada pode ser cancelada")
    aulas = _no_escopo(sessao, aula, escopo)
    for item in aulas:
        item.status = StatusAula.CANCELADA
        item.motivo_cancelamento = motivo
        _descartar_lembretes(sessao, item)
    if repor:
        sessao.execute(
            update(AulaAluno)
            .where(
                AulaAluno.aula_id.in_([item.id for item in aulas]),
                AulaAluno.status == StatusParticipacao.ATIVA,
            )
            .values(repor=True)
        )
    notificacao = None
    if aula.inicio > agora():
        tipo = (
            TipoNotificacao.AULAS_CANCELADAS
            if len(aulas) > 1
            else TipoNotificacao.AULA_CANCELADA
        )
        notificacao = notificacao_service.agendar(sessao, tipo, aula.id, agora())
    sessao.commit()
    return aula, notificacao.id if notificacao is not None else None


def adicionar_alunos(
    sessao: Session,
    professor: Usuario,
    aula_id: int,
    escopo: Escopo,
    *,
    aluno_ids: Sequence[int] = (),
    grupo_ids: Sequence[int] = (),
) -> Aula:
    """Levanta AulaNaoEncontrada, OperacaoNaoPermitida, AulaInvalida,
    AlunosInvalidos e GruposInvalidos, sem alterar nada."""
    aula = _aula_do_professor(sessao, professor, aula_id)
    _exigir_agendada(aula, "Só é possível mudar os alunos de uma aula agendada")
    participantes = _participantes(sessao, professor, aluno_ids, grupo_ids)
    if not participantes:
        raise AulaInvalida(
            "sem_aluno", "os grupos informados não têm alunos", ["grupo_ids"]
        )
    aulas = _no_escopo(sessao, aula, escopo)
    _vincular(sessao, [item.id for item in aulas], participantes, grupo_ids)
    sessao.commit()
    return aula


def remover_aluno(
    sessao: Session, professor: Usuario, aula_id: int, aluno_id: int, escopo: Escopo
) -> None:
    """Levanta AulaNaoEncontrada, OperacaoNaoPermitida e AlunoForaDaAula."""
    aula = _aula_do_professor(sessao, professor, aula_id)
    _exigir_agendada(aula, "Só é possível mudar os alunos de uma aula agendada")
    if sessao.get(AulaAluno, (aula.id, aluno_id)) is None:
        raise AlunoForaDaAula
    aulas = _no_escopo(sessao, aula, escopo)
    sessao.execute(
        delete(AulaAluno).where(
            AulaAluno.aula_id.in_([item.id for item in aulas]),
            AulaAluno.aluno_id == aluno_id,
        )
    )
    sessao.commit()


# --- reposições ---


def _pendente() -> list:
    return [AulaAluno.repor, AulaAluno.reposta_em_aula_id.is_(None)]


def listar_reposicoes_pendentes(
    sessao: Session, professor: Usuario, *, pagina: int, tamanho: int
) -> tuple[Sequence[Row], int]:
    """Alunos que ficaram sem aula, da aula mais antiga à mais nova, e o total."""
    pelo_aluno = AulaAluno.status == StatusParticipacao.CANCELADA
    pendentes = (
        select()
        .select_from(AulaAluno)
        .join(Aula, Aula.id == AulaAluno.aula_id)
        .join(Usuario, Usuario.id == AulaAluno.aluno_id)
        .where(
            Aula.professor_id == professor.id,
            Aula.deletado_em.is_(None),
            Usuario.deletado_em.is_(None),
            *_pendente(),
        )
    )
    total = sessao.scalar(pendentes.add_columns(func.count()))
    itens = sessao.execute(
        pendentes.add_columns(
            Aula.id.label("aula_id"),
            Aula.titulo,
            Aula.inicio,
            Aula.fim,
            Usuario.id.label("aluno_id"),
            Usuario.nome_completo.label("aluno_nome"),
            case((pelo_aluno, "aluno"), else_="professor").label("cancelada_por"),
            case(
                (pelo_aluno, AulaAluno.motivo_cancelamento),
                else_=Aula.motivo_cancelamento,
            ).label("motivo_cancelamento"),
        )
        .order_by(Aula.inicio, Aula.id, *ORDEM_DOS_ALUNOS)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def dispensar_reposicao(
    sessao: Session, professor: Usuario, aula_id: int, aluno_id: int
) -> None:
    """Tira a pendência sem criar aula. Levanta ReposicaoNaoEncontrada."""
    resultado = sessao.execute(
        update(AulaAluno)
        .where(
            AulaAluno.aula_id == aula_id,
            AulaAluno.aluno_id == aluno_id,
            AulaAluno.aula_id.in_(
                select(Aula.id).where(
                    Aula.professor_id == professor.id, Aula.deletado_em.is_(None)
                )
            ),
            *_pendente(),
        )
        .values(repor=False)
    )
    if resultado.rowcount == 0:
        raise ReposicaoNaoEncontrada
    sessao.commit()


# --- agenda do aluno ---


def _consulta_agenda(aluno: Usuario) -> Select:
    return (
        select(
            Aula.id,
            Aula.titulo,
            Aula.descricao,
            Aula.inicio,
            Aula.fim,
            Aula.status,
            AulaAluno.status.label("participacao"),
            Aula.motivo_cancelamento,
            Usuario.nome_completo.label("professor_nome"),
        )
        .join(AulaAluno, AulaAluno.aula_id == Aula.id)
        .join(Usuario, Usuario.id == Aula.professor_id)
        .where(AulaAluno.aluno_id == aluno.id, Aula.deletado_em.is_(None))
    )


def listar_agenda(
    sessao: Session,
    aluno: Usuario,
    *,
    data_inicio: date,
    data_fim: date,
    status: StatusAula | None = None,
) -> Sequence[Row]:
    """Aulas do aluno que começam no período. Levanta AulaInvalida."""
    de, ate = _periodo(data_inicio, data_fim)
    consulta = _consulta_agenda(aluno).where(Aula.inicio >= de, Aula.inicio < ate)
    if status is not None:
        consulta = consulta.where(Aula.status == status)
    return sessao.execute(consulta.order_by(Aula.inicio, Aula.id)).all()


def obter_da_agenda(sessao: Session, aluno: Usuario, aula_id: int) -> Row:
    """Levanta AulaNaoEncontrada."""
    item = sessao.execute(_consulta_agenda(aluno).where(Aula.id == aula_id)).first()
    if item is None:
        raise AulaNaoEncontrada
    return item


def cancelar_participacao(
    sessao: Session, aluno: Usuario, aula_id: int, motivo: str | None = None
) -> tuple[Row, int]:
    """O aluno sai da aula e fica com uma reposição pendente. O professor é avisado.

    Devolve a aula na agenda e o id da notificação do aviso.

    Levanta AulaNaoEncontrada e OperacaoNaoPermitida.
    """
    participacao = sessao.get(AulaAluno, (aula_id, aluno.id))
    aula = sessao.get(Aula, aula_id)
    if participacao is None or aula is None or aula.deletado_em is not None:
        raise AulaNaoEncontrada
    if aula.status != StatusAula.AGENDADA or aula.inicio <= agora():
        raise OperacaoNaoPermitida(
            "Só é possível cancelar uma aula agendada que ainda não começou"
        )
    if participacao.status == StatusParticipacao.CANCELADA:
        raise OperacaoNaoPermitida("Você já cancelou esta aula")
    participacao.status = StatusParticipacao.CANCELADA
    participacao.motivo_cancelamento = motivo
    participacao.cancelada_em = agora()
    participacao.repor = True
    notificacao = notificacao_service.agendar(
        sessao, TipoNotificacao.PARTICIPACAO_CANCELADA, participacao.id, agora()
    )
    sessao.commit()
    return obter_da_agenda(sessao, aluno, aula_id), notificacao.id


# --- notificações push ---


def _aula_e_professor(
    sessao: Session, aula_id: int, status: StatusAula
) -> tuple[Aula, Usuario] | None:
    """A aula, se ainda está no status esperado e não começou, e o professor ativo."""
    aula = sessao.get(Aula, aula_id)
    if (
        aula is None
        or aula.deletado_em is not None
        or aula.status != status
        or aula.inicio <= agora()
    ):
        return None
    professor = sessao.get(Usuario, aula.professor_id)
    if professor is None or professor.deletado_em is not None:
        return None
    return aula, professor


def _alunos_ativos(sessao: Session, aula: Aula) -> Sequence[int]:
    return sessao.scalars(
        consulta_alunos()
        .with_only_columns(Usuario.id)
        .join(AulaAluno, AulaAluno.aluno_id == Usuario.id)
        .where(
            AulaAluno.aula_id == aula.id,
            AulaAluno.status == StatusParticipacao.ATIVA,
        )
    ).all()


def _com_motivo(texto: str, motivo: str | None) -> str:
    return f"{texto} Motivo: {motivo}" if motivo else texto


def _resolvedor_de_lembrete(tipo: TipoNotificacao) -> notificacao_service.Resolvedor:
    _, titulo = LEMBRETES[tipo]

    def resolver(sessao: Session, aula_id: int) -> notificacao_service.Conteudo | None:
        encontrado = _aula_e_professor(sessao, aula_id, StatusAula.AGENDADA)
        if encontrado is None:
            return None
        aula, professor = encontrado
        return notificacao_service.Conteudo(
            usuario_ids=_alunos_ativos(sessao, aula),
            titulo=f"{titulo}: {aula.titulo}",
            corpo=f"{formatar_horario(aula.inicio)}, com {professor.nome_completo}",
            dados={"tipo": tipo.value, "aula_id": aula.id},
        )

    return resolver


def conteudo_da_aula_cancelada(
    sessao: Session, aula_id: int
) -> notificacao_service.Conteudo | None:
    """Avisa os alunos de uma aula futura cancelada pelo professor."""
    encontrado = _aula_e_professor(sessao, aula_id, StatusAula.CANCELADA)
    if encontrado is None:
        return None
    aula, _ = encontrado
    return notificacao_service.Conteudo(
        usuario_ids=_alunos_ativos(sessao, aula),
        titulo=f"Aula cancelada: {aula.titulo}",
        corpo=_com_motivo(
            f"A aula de {formatar_horario(aula.inicio)} foi cancelada.",
            aula.motivo_cancelamento,
        ),
        dados={"tipo": TipoNotificacao.AULA_CANCELADA.value, "aula_id": aula.id},
    )


def conteudo_das_aulas_canceladas(
    sessao: Session, aula_id: int
) -> notificacao_service.Conteudo | None:
    """Avisa, uma vez só, que a aula e as seguintes da série foram canceladas."""
    encontrado = _aula_e_professor(sessao, aula_id, StatusAula.CANCELADA)
    if encontrado is None:
        return None
    aula, _ = encontrado
    return notificacao_service.Conteudo(
        usuario_ids=_alunos_ativos(sessao, aula),
        titulo=f"Aulas canceladas: {aula.titulo}",
        corpo=_com_motivo(
            f"As aulas a partir de {formatar_horario(aula.inicio)} foram canceladas.",
            aula.motivo_cancelamento,
        ),
        dados={"tipo": TipoNotificacao.AULAS_CANCELADAS.value, "aula_id": aula.id},
    )


def conteudo_da_participacao_cancelada(
    sessao: Session, participacao_id: int
) -> notificacao_service.Conteudo | None:
    """Avisa o professor de que o aluno cancelou e precisa de reposição."""
    participacao = sessao.scalar(
        select(AulaAluno).where(AulaAluno.id == participacao_id)
    )
    if participacao is None or participacao.status != StatusParticipacao.CANCELADA:
        return None
    aula = sessao.get(Aula, participacao.aula_id)
    aluno = sessao.get(Usuario, participacao.aluno_id)
    if (
        aula is None
        or aula.deletado_em is not None
        or aula.status != StatusAula.AGENDADA
        or aluno is None
        or aluno.deletado_em is not None
    ):
        return None
    return notificacao_service.Conteudo(
        usuario_ids=[aula.professor_id],
        titulo=f"{aluno.nome_completo} cancelou a aula",
        corpo=_com_motivo(
            f"{aula.titulo}, {formatar_horario(aula.inicio)}.",
            participacao.motivo_cancelamento,
        ),
        dados={
            "tipo": TipoNotificacao.PARTICIPACAO_CANCELADA.value,
            "aula_id": aula.id,
            "aluno_id": aluno.id,
        },
    )


RESOLVEDORES: dict[TipoNotificacao, notificacao_service.Resolvedor] = {
    **{tipo: _resolvedor_de_lembrete(tipo) for tipo in LEMBRETES},
    TipoNotificacao.AULA_CANCELADA: conteudo_da_aula_cancelada,
    TipoNotificacao.AULAS_CANCELADAS: conteudo_das_aulas_canceladas,
    TipoNotificacao.PARTICIPACAO_CANCELADA: conteudo_da_participacao_cancelada,
}

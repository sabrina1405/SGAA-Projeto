import re
from collections.abc import Sequence
from datetime import date, datetime, time

from sqlalchemy import ColumnElement, Row, and_, delete, exists, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.security import agora
from src.models.grupo import Grupo, GrupoAluno
from src.models.notificacao import TipoNotificacao
from src.models.recado import Recado, RecadoAluno, RecadoGeral, RecadoGrupo
from src.models.usuario import Usuario
from src.schemas.aluno import HORARIO_DE_BRASILIA, hoje
from src.services import notificacao_service
from src.services.usuario_service import (
    ORDEM_DOS_ALUNOS,
    consulta_alunos,
    validar_alunos,
)


class RecadoNaoEncontrado(Exception):
    pass


class GruposInvalidos(Exception):
    def __init__(self, ids: list[int]) -> None:
        super().__init__(ids)
        self.ids = ids


class RecadoInvalido(Exception):
    """Regra que depende do recado inteiro, e não de um campo só."""

    def __init__(self, tipo: str, mensagem: str, campos: list[str]) -> None:
        super().__init__(mensagem)
        self.tipo = tipo
        self.mensagem = mensagem
        self.campos = campos


# --- recado geral ---


def obter_recado_geral(sessao: Session, professor: Usuario) -> RecadoGeral | None:
    """None quando o painel está vazio."""
    recado_geral = sessao.get(RecadoGeral, professor.id)
    if recado_geral is None or recado_geral.deletado_em is not None:
        return None
    return recado_geral


def salvar_recado_geral(
    sessao: Session, professor: Usuario, conteudo: str
) -> RecadoGeral:
    recado_geral = sessao.get(RecadoGeral, professor.id)
    if recado_geral is None:
        recado_geral = RecadoGeral(professor_id=professor.id)
        sessao.add(recado_geral)
    recado_geral.conteudo = conteudo
    recado_geral.deletado_em = None
    sessao.commit()
    return recado_geral


def limpar_recado_geral(sessao: Session, professor: Usuario) -> None:
    """Esvaziar um painel já vazio não é erro."""
    recado_geral = obter_recado_geral(sessao, professor)
    if recado_geral is not None:
        recado_geral.deletado_em = agora()
        sessao.commit()


# --- recados do professor ---


def _recado_do_professor(sessao: Session, professor: Usuario, recado_id: int) -> Recado:
    recado = sessao.get(Recado, recado_id)
    if (
        recado is None
        or recado.deletado_em is not None
        or recado.professor_id != professor.id
    ):
        raise RecadoNaoEncontrado
    return recado


def _validar_grupos(
    sessao: Session, professor: Usuario, grupo_ids: Sequence[int]
) -> None:
    """Levanta GruposInvalidos com os ids que não são de grupos do professor."""
    if not grupo_ids:
        return
    validos = set(
        sessao.scalars(
            select(Grupo.id).where(
                Grupo.id.in_(grupo_ids),
                Grupo.professor_id == professor.id,
                Grupo.deletado_em.is_(None),
            )
        )
    )
    invalidos = [grupo_id for grupo_id in grupo_ids if grupo_id not in validos]
    if invalidos:
        raise GruposInvalidos(invalidos)


def _conferir_recado(
    *,
    data_inicio: date,
    data_fim: date | None,
    todos_alunos: bool,
    todos_grupos: bool,
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> None:
    """Levanta RecadoInvalido. Recebe o recado como vai ficar no banco."""
    if data_fim is not None and data_fim < data_inicio:
        raise RecadoInvalido(
            "periodo_invalido",
            "a data de fim não pode ser anterior à data de início",
            ["data_fim"],
        )
    if todos_alunos and aluno_ids:
        raise RecadoInvalido(
            "destinatarios_conflitantes",
            "com todos os alunos marcados, não informe alunos avulsos",
            ["aluno_ids"],
        )
    if todos_grupos and grupo_ids:
        raise RecadoInvalido(
            "destinatarios_conflitantes",
            "com todos os grupos marcados, não informe grupos avulsos",
            ["grupo_ids"],
        )
    if not (todos_alunos or todos_grupos or aluno_ids or grupo_ids):
        raise RecadoInvalido(
            "sem_destinatario",
            "informe ao menos um aluno ou grupo destinatário",
            ["aluno_ids", "grupo_ids"],
        )


def _vincular(
    sessao: Session,
    recado: Recado,
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> None:
    if aluno_ids:
        sessao.execute(
            insert(RecadoAluno)
            .values(
                [
                    {"recado_id": recado.id, "aluno_id": aluno_id}
                    for aluno_id in aluno_ids
                ]
            )
            .on_conflict_do_nothing()
        )
    if grupo_ids:
        sessao.execute(
            insert(RecadoGrupo)
            .values(
                [
                    {"recado_id": recado.id, "grupo_id": grupo_id}
                    for grupo_id in grupo_ids
                ]
            )
            .on_conflict_do_nothing()
        )


def criar_recado(
    sessao: Session,
    professor: Usuario,
    *,
    conteudo: str,
    data_inicio: date,
    data_fim: date | None = None,
    todos_alunos: bool = False,
    todos_grupos: bool = False,
    aluno_ids: Sequence[int] = (),
    grupo_ids: Sequence[int] = (),
) -> Recado:
    """Levanta RecadoInvalido, AlunosInvalidos e GruposInvalidos, sem criar o recado."""
    _conferir_recado(
        data_inicio=data_inicio,
        data_fim=data_fim,
        todos_alunos=todos_alunos,
        todos_grupos=todos_grupos,
        aluno_ids=aluno_ids,
        grupo_ids=grupo_ids,
    )
    validar_alunos(sessao, aluno_ids)
    _validar_grupos(sessao, professor, grupo_ids)
    recado = Recado(
        professor_id=professor.id,
        conteudo=conteudo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        todos_alunos=todos_alunos,
        todos_grupos=todos_grupos,
    )
    sessao.add(recado)
    sessao.flush()
    _vincular(sessao, recado, aluno_ids, grupo_ids)
    notificacao_service.agendar(
        sessao, TipoNotificacao.RECADO, recado.id, _momento_do_aviso(data_inicio)
    )
    sessao.commit()
    return recado


def listar_recados(
    sessao: Session, professor: Usuario, *, pagina: int, tamanho: int
) -> tuple[Sequence[Row], int]:
    """Página do histórico do professor, do mais novo ao mais antigo, e o total."""
    do_professor = (Recado.professor_id == professor.id, Recado.deletado_em.is_(None))
    total_alunos = (
        select(func.count())
        .select_from(RecadoAluno)
        .join(Usuario, Usuario.id == RecadoAluno.aluno_id)
        .where(RecadoAluno.recado_id == Recado.id, Usuario.deletado_em.is_(None))
        .correlate(Recado)
        .scalar_subquery()
    )
    total_grupos = (
        select(func.count())
        .select_from(RecadoGrupo)
        .join(Grupo, Grupo.id == RecadoGrupo.grupo_id)
        .where(RecadoGrupo.recado_id == Recado.id, Grupo.deletado_em.is_(None))
        .correlate(Recado)
        .scalar_subquery()
    )

    total = sessao.scalar(select(func.count()).select_from(Recado).where(*do_professor))
    itens = sessao.execute(
        select(
            Recado.id,
            Recado.conteudo,
            Recado.data_inicio,
            Recado.data_fim,
            Recado.todos_alunos,
            Recado.todos_grupos,
            total_alunos.label("total_alunos"),
            total_grupos.label("total_grupos"),
            Recado.criado_em,
        )
        .where(*do_professor)
        .order_by(Recado.criado_em.desc(), Recado.id.desc())
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_recado(sessao: Session, professor: Usuario, recado_id: int) -> Recado:
    """Levanta RecadoNaoEncontrado."""
    return _recado_do_professor(sessao, professor, recado_id)


def listar_alunos_do_recado(sessao: Session, recado: Recado) -> Sequence[Row]:
    return sessao.execute(
        consulta_alunos()
        .join(RecadoAluno, RecadoAluno.aluno_id == Usuario.id)
        .where(RecadoAluno.recado_id == recado.id)
        .order_by(*ORDEM_DOS_ALUNOS)
    ).all()


def listar_grupos_do_recado(sessao: Session, recado: Recado) -> Sequence[Row]:
    return sessao.execute(
        select(Grupo.id, Grupo.titulo)
        .join(RecadoGrupo, RecadoGrupo.grupo_id == Grupo.id)
        .where(RecadoGrupo.recado_id == recado.id, Grupo.deletado_em.is_(None))
        .order_by(func.lower(func.unaccent(Grupo.titulo)), Grupo.id)
    ).all()


def atualizar_recado(
    sessao: Session, professor: Usuario, recado_id: int, campos: dict
) -> Recado:
    """Altera os campos presentes em `campos`. `aluno_ids` e `grupo_ids`
    substituem os destinatários.

    Levanta RecadoNaoEncontrado, RecadoInvalido, AlunosInvalidos e
    GruposInvalidos, sem alterar nada.
    """
    recado = _recado_do_professor(sessao, professor, recado_id)
    # Só as listas enviadas são validadas: um aluno excluído depois do envio
    # não impede editar o texto do recado.
    aluno_ids_enviados = campos.pop("aluno_ids", None)
    grupo_ids_enviados = campos.pop("grupo_ids", None)
    aluno_ids = aluno_ids_enviados
    if aluno_ids is None:
        aluno_ids = sessao.scalars(
            select(RecadoAluno.aluno_id).where(RecadoAluno.recado_id == recado.id)
        ).all()
    grupo_ids = grupo_ids_enviados
    if grupo_ids is None:
        grupo_ids = sessao.scalars(
            select(RecadoGrupo.grupo_id).where(RecadoGrupo.recado_id == recado.id)
        ).all()

    _conferir_recado(
        data_inicio=campos.get("data_inicio", recado.data_inicio),
        data_fim=campos.get("data_fim", recado.data_fim),
        todos_alunos=campos.get("todos_alunos", recado.todos_alunos),
        todos_grupos=campos.get("todos_grupos", recado.todos_grupos),
        aluno_ids=aluno_ids,
        grupo_ids=grupo_ids,
    )
    if aluno_ids_enviados is not None:
        validar_alunos(sessao, aluno_ids_enviados)
    if grupo_ids_enviados is not None:
        _validar_grupos(sessao, professor, grupo_ids_enviados)

    for campo, valor in campos.items():
        setattr(recado, campo, valor)
    if "data_inicio" in campos:
        # Só muda o que ainda não foi enviado: editar não avisa de novo.
        notificacao_service.reagendar(
            sessao,
            TipoNotificacao.RECADO,
            recado.id,
            _momento_do_aviso(recado.data_inicio),
        )
    if aluno_ids_enviados is not None:
        sessao.execute(delete(RecadoAluno).where(RecadoAluno.recado_id == recado.id))
        _vincular(sessao, recado, aluno_ids_enviados, ())
    if grupo_ids_enviados is not None:
        sessao.execute(delete(RecadoGrupo).where(RecadoGrupo.recado_id == recado.id))
        _vincular(sessao, recado, (), grupo_ids_enviados)
    sessao.commit()
    return recado


def excluir_recado(sessao: Session, professor: Usuario, recado_id: int) -> None:
    """Soft delete: os vínculos com os destinatários ficam no banco.

    Levanta RecadoNaoEncontrado.
    """
    recado = _recado_do_professor(sessao, professor, recado_id)
    recado.deletado_em = agora()
    sessao.commit()


# --- mural do aluno ---


def listar_recados_gerais(sessao: Session) -> Sequence[Row]:
    """Painéis preenchidos de professores ativos, do mais recente ao mais antigo."""
    return sessao.execute(
        select(
            Usuario.nome_completo.label("professor_nome"),
            RecadoGeral.conteudo,
            RecadoGeral.atualizado_em,
        )
        .join(Usuario, Usuario.id == RecadoGeral.professor_id)
        .where(RecadoGeral.deletado_em.is_(None), Usuario.deletado_em.is_(None))
        .order_by(RecadoGeral.atualizado_em.desc(), RecadoGeral.professor_id)
    ).all()


def _destinado_a(aluno_id: int | ColumnElement[int]) -> ColumnElement[bool]:
    """Se o recado (correlacionado na consulta externa) aparece para o aluno.

    `aluno_id` pode ser uma coluna, para buscar todos os alunos de um recado.
    """
    em_grupo_ativo = and_(
        GrupoAluno.grupo_id == Grupo.id,
        GrupoAluno.aluno_id == aluno_id,
        Grupo.deletado_em.is_(None),
    )
    return or_(
        Recado.todos_alunos,
        and_(
            Recado.todos_grupos,
            exists().where(em_grupo_ativo, Grupo.professor_id == Recado.professor_id),
        ),
        exists().where(
            RecadoAluno.recado_id == Recado.id, RecadoAluno.aluno_id == aluno_id
        ),
        exists().where(
            RecadoGrupo.recado_id == Recado.id,
            RecadoGrupo.grupo_id == Grupo.id,
            em_grupo_ativo,
        ),
    )


def listar_mural(
    sessao: Session, aluno: Usuario, *, pagina: int, tamanho: int
) -> tuple[Sequence[Row], int]:
    """Recados no período de exibição destinados ao aluno, do início mais recente
    ao mais antigo, e o total sem paginar."""
    data = hoje()
    filtros = (
        Recado.deletado_em.is_(None),
        Usuario.deletado_em.is_(None),
        Recado.data_inicio <= data,
        or_(Recado.data_fim.is_(None), Recado.data_fim >= data),
        _destinado_a(aluno.id),
    )
    do_mural = (
        select()
        .select_from(Recado)
        .join(Usuario, Usuario.id == Recado.professor_id)
        .where(*filtros)
    )

    total = sessao.scalar(do_mural.add_columns(func.count()))
    itens = sessao.execute(
        do_mural.add_columns(
            Recado.id,
            Recado.conteudo,
            Recado.data_inicio,
            Recado.data_fim,
            Usuario.nome_completo.label("professor_nome"),
            Recado.criado_em,
        )
        .order_by(Recado.data_inicio.desc(), Recado.id.desc())
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


# --- notificação push ---

HORA_DO_AVISO_AGENDADO = time(7, tzinfo=HORARIO_DE_BRASILIA)
TAMANHO_DO_RESUMO = 120


def _momento_do_aviso(data_inicio: date) -> datetime:
    """Recado que já começou é avisado na hora; o futuro, no dia, às 7h."""
    if data_inicio <= hoje():
        return agora()
    return datetime.combine(data_inicio, HORA_DO_AVISO_AGENDADO)


def _resumo(conteudo: str) -> str:
    """Texto curto para a notificação, sem a marcação mais comum do Markdown."""
    texto = " ".join(re.sub(r"[*_#>`~]", "", conteudo).split())
    if len(texto) <= TAMANHO_DO_RESUMO:
        return texto
    return texto[: TAMANHO_DO_RESUMO - 1].rstrip() + "…"


def conteudo_da_notificacao(
    sessao: Session, recado_id: int
) -> notificacao_service.Conteudo | None:
    """Resolvedor do push de recado novo: os alunos que veem o recado no mural.

    None se o recado foi excluído ou não está no período de exibição.
    """
    recado = sessao.get(Recado, recado_id)
    data = hoje()
    if (
        recado is None
        or recado.deletado_em is not None
        or recado.data_inicio > data
        or (recado.data_fim is not None and recado.data_fim < data)
    ):
        return None
    professor = sessao.get(Usuario, recado.professor_id)
    if professor is None or professor.deletado_em is not None:
        return None
    usuario_ids = sessao.scalars(
        consulta_alunos()
        .with_only_columns(Usuario.id)
        .join(Recado, Recado.id == recado.id)
        .where(_destinado_a(Usuario.id))
    ).all()
    return notificacao_service.Conteudo(
        usuario_ids=usuario_ids,
        titulo=f"Novo recado de {professor.nome_completo}",
        corpo=_resumo(recado.conteudo),
        dados={"tipo": TipoNotificacao.RECADO.value, "recado_id": recado.id},
    )

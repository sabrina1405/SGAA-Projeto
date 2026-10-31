from collections.abc import Sequence
from datetime import date

from sqlalchemy import ColumnElement, Row, and_, delete, exists, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.security import agora
from src.models.grupo import Grupo, GrupoAluno
from src.models.recado import Recado, RecadoAluno, RecadoGeral, RecadoGrupo
from src.models.usuario import Usuario
from src.schemas.aluno import hoje
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


def _destinado_ao_aluno(aluno: Usuario) -> ColumnElement[bool]:
    em_grupo_ativo = and_(
        GrupoAluno.grupo_id == Grupo.id,
        GrupoAluno.aluno_id == aluno.id,
        Grupo.deletado_em.is_(None),
    )
    return or_(
        Recado.todos_alunos,
        and_(
            Recado.todos_grupos,
            exists().where(em_grupo_ativo, Grupo.professor_id == Recado.professor_id),
        ),
        exists().where(
            RecadoAluno.recado_id == Recado.id, RecadoAluno.aluno_id == aluno.id
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
        _destinado_ao_aluno(aluno),
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

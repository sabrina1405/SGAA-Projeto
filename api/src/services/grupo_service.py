from collections.abc import Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.security import agora
from src.models.grupo import Grupo, GrupoAluno
from src.models.usuario import Usuario
from src.services.usuario_service import ORDEM_DOS_ALUNOS, consulta_alunos


class GrupoNaoEncontrado(Exception):
    pass


class AlunoForaDoGrupo(Exception):
    pass


class AlunosInvalidos(Exception):
    def __init__(self, ids: list[int]) -> None:
        super().__init__(ids)
        self.ids = ids


def _grupo_do_professor(sessao: Session, professor: Usuario, grupo_id: int) -> Grupo:
    grupo = sessao.get(Grupo, grupo_id)
    if (
        grupo is None
        or grupo.deletado_em is not None
        or grupo.professor_id != professor.id
    ):
        raise GrupoNaoEncontrado
    return grupo


def _validar_alunos(sessao: Session, aluno_ids: Sequence[int]) -> None:
    """Levanta AlunosInvalidos com os ids que não são de alunos ativos."""
    if not aluno_ids:
        return
    validos = set(
        sessao.scalars(
            consulta_alunos()
            .with_only_columns(Usuario.id)
            .where(Usuario.id.in_(aluno_ids))
        )
    )
    invalidos = [aluno_id for aluno_id in aluno_ids if aluno_id not in validos]
    if invalidos:
        raise AlunosInvalidos(invalidos)


def _vincular(sessao: Session, grupo: Grupo, aluno_ids: Sequence[int]) -> None:
    if not aluno_ids:
        return
    # Quem já está no grupo é ignorado, inclusive em chamadas simultâneas.
    sessao.execute(
        insert(GrupoAluno)
        .values(
            [{"grupo_id": grupo.id, "aluno_id": aluno_id} for aluno_id in aluno_ids]
        )
        .on_conflict_do_nothing()
    )


def criar_grupo(
    sessao: Session,
    professor: Usuario,
    *,
    titulo: str,
    descricao: str | None = None,
    aluno_ids: Sequence[int] = (),
) -> Grupo:
    """Levanta AlunosInvalidos, sem criar o grupo."""
    _validar_alunos(sessao, aluno_ids)
    grupo = Grupo(titulo=titulo, descricao=descricao, professor_id=professor.id)
    sessao.add(grupo)
    sessao.flush()
    _vincular(sessao, grupo, aluno_ids)
    sessao.commit()
    return grupo


def listar_grupos(
    sessao: Session, professor: Usuario, *, pagina: int, tamanho: int
) -> tuple[Sequence[Row], int]:
    """Página dos grupos do professor, por título, e o total sem paginar."""
    do_professor = (Grupo.professor_id == professor.id, Grupo.deletado_em.is_(None))
    total_alunos = (
        select(func.count())
        .select_from(GrupoAluno)
        .join(Usuario, Usuario.id == GrupoAluno.aluno_id)
        .where(GrupoAluno.grupo_id == Grupo.id, Usuario.deletado_em.is_(None))
        .correlate(Grupo)
        .scalar_subquery()
    )

    total = sessao.scalar(select(func.count()).select_from(Grupo).where(*do_professor))
    itens = sessao.execute(
        select(
            Grupo.id, Grupo.titulo, Grupo.descricao, total_alunos.label("total_alunos")
        )
        .where(*do_professor)
        .order_by(func.lower(func.unaccent(Grupo.titulo)), Grupo.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_grupo(sessao: Session, professor: Usuario, grupo_id: int) -> Grupo:
    """Levanta GrupoNaoEncontrado."""
    return _grupo_do_professor(sessao, professor, grupo_id)


def listar_alunos_do_grupo(sessao: Session, grupo: Grupo) -> Sequence[Row]:
    return sessao.execute(
        consulta_alunos()
        .join(GrupoAluno, GrupoAluno.aluno_id == Usuario.id)
        .where(GrupoAluno.grupo_id == grupo.id)
        .order_by(*ORDEM_DOS_ALUNOS)
    ).all()


def atualizar_grupo(
    sessao: Session, professor: Usuario, grupo_id: int, campos: dict[str, str | None]
) -> Grupo:
    """Altera `titulo` e `descricao` presentes em `campos`.

    Levanta GrupoNaoEncontrado.
    """
    grupo = _grupo_do_professor(sessao, professor, grupo_id)
    for campo, valor in campos.items():
        setattr(grupo, campo, valor)
    sessao.commit()
    return grupo


def excluir_grupo(sessao: Session, professor: Usuario, grupo_id: int) -> None:
    """Soft delete: os vínculos com os alunos ficam no banco.

    Levanta GrupoNaoEncontrado.
    """
    grupo = _grupo_do_professor(sessao, professor, grupo_id)
    grupo.deletado_em = agora()
    sessao.commit()


def adicionar_alunos(
    sessao: Session, professor: Usuario, grupo_id: int, aluno_ids: Sequence[int]
) -> Grupo:
    """Levanta GrupoNaoEncontrado e AlunosInvalidos, sem adicionar nenhum."""
    grupo = _grupo_do_professor(sessao, professor, grupo_id)
    _validar_alunos(sessao, aluno_ids)
    _vincular(sessao, grupo, aluno_ids)
    sessao.commit()
    return grupo


def remover_aluno(
    sessao: Session, professor: Usuario, grupo_id: int, aluno_id: int
) -> None:
    """Levanta GrupoNaoEncontrado e AlunoForaDoGrupo."""
    grupo = _grupo_do_professor(sessao, professor, grupo_id)
    vinculo = sessao.get(GrupoAluno, (grupo.id, aluno_id))
    if vinculo is None:
        raise AlunoForaDoGrupo
    sessao.delete(vinculo)
    sessao.commit()

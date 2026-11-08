"""Pastas de materiais (apostilas) do professor e a visão do aluno.

Os destinatários ficam na pasta raiz e valem para toda a árvore abaixo dela:
cada pasta guarda `raiz_id`, então conferir quem vê não sobe a árvore.
"""

from collections.abc import Sequence

from sqlalchemy import (
    ColumnElement,
    Row,
    and_,
    delete,
    exists,
    func,
    literal,
    or_,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from src.core.security import agora
from src.models.arquivo import Arquivo, StatusArquivo
from src.models.grupo import Grupo, GrupoAluno
from src.models.material import AnexoPasta, Pasta, PastaAluno, PastaGrupo
from src.models.professor import Professor
from src.models.usuario import Usuario
from src.services import arquivo_service
from src.services.grupo_service import validar_grupos
from src.services.usuario_service import (
    ORDEM_DOS_ALUNOS,
    consulta_alunos,
    validar_alunos,
)

# Trava de segurança: sem ela, uma árvore muito funda deixaria as consultas
# recursivas sem limite. Pode subir se o uso real pedir.
PROFUNDIDADE_MAXIMA = 20

DESTINATARIOS = ("todos_alunos", "todos_grupos", "aluno_ids", "grupo_ids")


class PastaNaoEncontrada(Exception):
    pass


class ArquivoForaDaPasta(Exception):
    pass


class NomeDePastaRepetido(Exception):
    pass


class PastaInvalida(Exception):
    """Regra que depende da pasta inteira, e não de um campo só."""

    def __init__(self, tipo: str, mensagem: str, campos: list[str]) -> None:
        super().__init__(mensagem)
        self.tipo = tipo
        self.mensagem = mensagem
        self.campos = campos


# --- árvore ---


def _pasta_do_professor(sessao: Session, professor: Usuario, pasta_id: int) -> Pasta:
    pasta = sessao.get(Pasta, pasta_id)
    if (
        pasta is None
        or pasta.deletado_em is not None
        or pasta.professor_id != professor.id
    ):
        raise PastaNaoEncontrada
    return pasta


def _pasta_de_destino(
    sessao: Session, professor: Usuario, pasta_id: int, campo: str
) -> Pasta:
    """Pasta informada no corpo: a de outro professor é um campo inválido."""
    try:
        return _pasta_do_professor(sessao, professor, pasta_id)
    except PastaNaoEncontrada:
        raise PastaInvalida(
            "pasta_invalida", f"pasta não encontrada: {pasta_id}", [campo]
        ) from None


def _travar_arvore(sessao: Session, professor_id: int) -> None:
    """Enfileira as mudanças de estrutura do professor, para que dois movimentos
    simultâneos não criem um ciclo."""
    sessao.execute(
        select(Professor.usuario_id)
        .where(Professor.usuario_id == professor_id)
        .with_for_update()
    )


def _descendentes(pasta_id: int):
    """CTE com a pasta e todas as subpastas ativas, com o nível relativo."""
    base = (
        select(Pasta.id, literal(0).label("nivel"))
        .where(Pasta.id == pasta_id)
        .cte("descendentes", recursive=True)
    )
    filha = aliased(Pasta)
    return base.union_all(
        select(filha.id, base.c.nivel + 1).where(
            filha.pasta_pai_id == base.c.id, filha.deletado_em.is_(None)
        )
    )


def _ancestrais(pasta_id: int):
    """CTE com a pasta e as pastas acima dela, com a distância até ela."""
    base = (
        select(Pasta.id, Pasta.pasta_pai_id, Pasta.nome, literal(0).label("nivel"))
        .where(Pasta.id == pasta_id)
        .cte("ancestrais", recursive=True)
    )
    pai = aliased(Pasta)
    return base.union_all(
        select(pai.id, pai.pasta_pai_id, pai.nome, base.c.nivel + 1).where(
            pai.id == base.c.pasta_pai_id
        )
    )


def _profundidade(sessao: Session, pasta_id: int) -> int:
    """1 na raiz."""
    return sessao.scalar(select(func.count()).select_from(_ancestrais(pasta_id)))


def _altura(sessao: Session, pasta_id: int) -> int:
    """Níveis da subárvore, contando a própria pasta."""
    cte = _descendentes(pasta_id)
    return sessao.scalar(select(func.max(cte.c.nivel))) + 1


def caminho(sessao: Session, pasta: Pasta) -> Sequence[Row]:
    """Da raiz até a pasta, para o app montar a navegação."""
    cte = _ancestrais(pasta.id)
    return sessao.execute(
        select(cte.c.id, cte.c.nome).order_by(cte.c.nivel.desc())
    ).all()


def _conferir_profundidade(sessao: Session, pai: Pasta, altura: int = 1) -> None:
    if _profundidade(sessao, pai.id) + altura > PROFUNDIDADE_MAXIMA:
        raise PastaInvalida(
            "profundidade_maxima",
            f"as pastas podem ter no máximo {PROFUNDIDADE_MAXIMA} níveis",
            ["pasta_pai_id"],
        )


def _conferir_nome(
    sessao: Session,
    professor: Usuario,
    nome: str,
    pasta_pai_id: int | None,
    ignorar_id: int | None = None,
) -> None:
    repetida = sessao.scalar(
        select(Pasta.id).where(
            Pasta.professor_id == professor.id,
            Pasta.deletado_em.is_(None),
            func.coalesce(Pasta.pasta_pai_id, 0) == (pasta_pai_id or 0),
            func.lower(Pasta.nome) == nome.lower(),
            Pasta.id != (ignorar_id or 0),
        )
    )
    if repetida is not None:
        raise NomeDePastaRepetido


def _gravar(sessao: Session) -> None:
    """Flush que converte a corrida no índice único de nome em NomeDePastaRepetido."""
    try:
        sessao.flush()
    except IntegrityError as erro:
        sessao.rollback()
        raise NomeDePastaRepetido from erro


# --- destinatários ---


def _conferir_destinatarios(
    *,
    todos_alunos: bool,
    todos_grupos: bool,
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> None:
    """Sem destinatário, a pasta é só da professora até ela liberar."""
    if todos_alunos and aluno_ids:
        raise PastaInvalida(
            "destinatarios_conflitantes",
            "com todos os alunos marcados, não informe alunos avulsos",
            ["aluno_ids"],
        )
    if todos_grupos and grupo_ids:
        raise PastaInvalida(
            "destinatarios_conflitantes",
            "com todos os grupos marcados, não informe grupos avulsos",
            ["grupo_ids"],
        )


def _destinatarios_so_na_raiz(campos: Sequence[str]) -> PastaInvalida:
    return PastaInvalida(
        "destinatarios_so_na_raiz",
        "os destinatários são definidos na pasta raiz e valem para as subpastas",
        list(campos),
    )


def _vincular(
    sessao: Session, pasta: Pasta, aluno_ids: Sequence[int], grupo_ids: Sequence[int]
) -> None:
    if aluno_ids:
        sessao.execute(
            insert(PastaAluno)
            .values([{"pasta_id": pasta.id, "aluno_id": item} for item in aluno_ids])
            .on_conflict_do_nothing()
        )
    if grupo_ids:
        sessao.execute(
            insert(PastaGrupo)
            .values([{"pasta_id": pasta.id, "grupo_id": item} for item in grupo_ids])
            .on_conflict_do_nothing()
        )


def _limpar_destinatarios(sessao: Session, pasta: Pasta) -> None:
    pasta.todos_alunos = False
    pasta.todos_grupos = False
    sessao.execute(delete(PastaAluno).where(PastaAluno.pasta_id == pasta.id))
    sessao.execute(delete(PastaGrupo).where(PastaGrupo.pasta_id == pasta.id))


def listar_alunos_da_pasta(sessao: Session, raiz_id: int) -> Sequence[Row]:
    return sessao.execute(
        consulta_alunos()
        .join(PastaAluno, PastaAluno.aluno_id == Usuario.id)
        .where(PastaAluno.pasta_id == raiz_id)
        .order_by(*ORDEM_DOS_ALUNOS)
    ).all()


def listar_grupos_da_pasta(sessao: Session, raiz_id: int) -> Sequence[Row]:
    return sessao.execute(
        select(Grupo.id, Grupo.titulo)
        .join(PastaGrupo, PastaGrupo.grupo_id == Grupo.id)
        .where(PastaGrupo.pasta_id == raiz_id, Grupo.deletado_em.is_(None))
        .order_by(func.lower(func.unaccent(Grupo.titulo)), Grupo.id)
    ).all()


# --- pastas do professor ---


def criar_pasta(
    sessao: Session,
    professor: Usuario,
    *,
    nome: str,
    pasta_pai_id: int | None = None,
    todos_alunos: bool = False,
    todos_grupos: bool = False,
    aluno_ids: Sequence[int] = (),
    grupo_ids: Sequence[int] = (),
) -> Pasta:
    """Levanta PastaInvalida, NomeDePastaRepetido, AlunosInvalidos e
    GruposInvalidos, sem criar a pasta."""
    _travar_arvore(sessao, professor.id)
    pai = None
    if pasta_pai_id is not None:
        pai = _pasta_de_destino(sessao, professor, pasta_pai_id, "pasta_pai_id")
        valores = (todos_alunos, todos_grupos, aluno_ids, grupo_ids)
        enviados = [campo for campo, valor in zip(DESTINATARIOS, valores) if valor]
        if enviados:
            raise _destinatarios_so_na_raiz(enviados)
        _conferir_profundidade(sessao, pai)
    _conferir_destinatarios(
        todos_alunos=todos_alunos,
        todos_grupos=todos_grupos,
        aluno_ids=aluno_ids,
        grupo_ids=grupo_ids,
    )
    validar_alunos(sessao, aluno_ids)
    validar_grupos(sessao, professor, grupo_ids)
    _conferir_nome(sessao, professor, nome, pasta_pai_id)

    pasta = Pasta(
        professor_id=professor.id,
        pasta_pai_id=pasta_pai_id,
        raiz_id=pai.raiz_id if pai is not None else None,
        nome=nome,
        todos_alunos=todos_alunos,
        todos_grupos=todos_grupos,
    )
    sessao.add(pasta)
    _gravar(sessao)
    if pai is None:
        pasta.raiz_id = pasta.id
    _vincular(sessao, pasta, aluno_ids, grupo_ids)
    sessao.commit()
    return pasta


def _totais():
    """Subpastas ativas e materiais de cada pasta da consulta externa."""
    filha = aliased(Pasta)
    total_subpastas = (
        select(func.count())
        .select_from(filha)
        .where(filha.pasta_pai_id == Pasta.id, filha.deletado_em.is_(None))
        .correlate(Pasta)
        .scalar_subquery()
    )
    total_arquivos = (
        select(func.count())
        .select_from(AnexoPasta)
        .join(Arquivo, Arquivo.id == AnexoPasta.arquivo_id)
        .where(
            AnexoPasta.pasta_id == Pasta.id,
            Arquivo.deletado_em.is_(None),
            Arquivo.status == StatusArquivo.CONFIRMADO,
        )
        .correlate(Pasta)
        .scalar_subquery()
    )
    return total_subpastas.label("total_subpastas"), total_arquivos.label(
        "total_arquivos"
    )


ORDEM_DAS_PASTAS = (func.lower(func.unaccent(Pasta.nome)), Pasta.id)


def listar_pastas(
    sessao: Session,
    professor: Usuario,
    *,
    pasta_pai_id: int | None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    """Pastas raiz, ou as filhas de `pasta_pai_id`, em ordem alfabética.

    Levanta PastaNaoEncontrada quando `pasta_pai_id` não é do professor.
    """
    if pasta_pai_id is not None:
        _pasta_do_professor(sessao, professor, pasta_pai_id)
    filtros = (
        Pasta.professor_id == professor.id,
        Pasta.deletado_em.is_(None),
        Pasta.pasta_pai_id.is_(None)
        if pasta_pai_id is None
        else Pasta.pasta_pai_id == pasta_pai_id,
    )
    total = sessao.scalar(select(func.count()).select_from(Pasta).where(*filtros))
    itens = sessao.execute(
        select(Pasta.id, Pasta.nome, *_totais(), Pasta.criado_em)
        .where(*filtros)
        .order_by(*ORDEM_DAS_PASTAS)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def listar_subpastas(sessao: Session, pasta: Pasta) -> Sequence[Row]:
    return sessao.execute(
        select(Pasta.id, Pasta.nome, *_totais(), Pasta.criado_em)
        .where(Pasta.pasta_pai_id == pasta.id, Pasta.deletado_em.is_(None))
        .order_by(*ORDEM_DAS_PASTAS)
    ).all()


def listar_arquivos(sessao: Session, pasta: Pasta) -> Sequence[Arquivo]:
    return sessao.scalars(
        select(Arquivo)
        .join(AnexoPasta, AnexoPasta.arquivo_id == Arquivo.id)
        .where(
            AnexoPasta.pasta_id == pasta.id,
            Arquivo.deletado_em.is_(None),
            Arquivo.status == StatusArquivo.CONFIRMADO,
        )
        .order_by(func.lower(func.unaccent(Arquivo.nome)), Arquivo.id)
    ).all()


def obter_pasta(sessao: Session, professor: Usuario, pasta_id: int) -> Pasta:
    """Levanta PastaNaoEncontrada."""
    return _pasta_do_professor(sessao, professor, pasta_id)


def obter_raiz(sessao: Session, pasta: Pasta) -> Pasta:
    return pasta if pasta.raiz_id == pasta.id else sessao.get(Pasta, pasta.raiz_id)


def _mover(sessao: Session, professor: Usuario, pasta: Pasta, destino_id: int | None):
    """Muda a pasta de lugar e acerta o `raiz_id` da subárvore inteira."""
    if destino_id is None:
        nova_raiz_id = pasta.id
    else:
        destino = _pasta_de_destino(sessao, professor, destino_id, "pasta_pai_id")
        dentro_dela = sessao.scalar(
            select(exists().where(_descendentes(pasta.id).c.id == destino.id))
        )
        if dentro_dela:
            raise PastaInvalida(
                "ciclo",
                "a pasta não pode ir para dentro dela mesma",
                ["pasta_pai_id"],
            )
        _conferir_profundidade(sessao, destino, _altura(sessao, pasta.id))
        nova_raiz_id = destino.raiz_id
    era_raiz = pasta.pasta_pai_id is None
    pasta.pasta_pai_id = destino_id
    if nova_raiz_id != pasta.raiz_id:
        subarvore = select(_descendentes(pasta.id).c.id)
        sessao.execute(
            update(Pasta)
            .where(Pasta.id.in_(subarvore))
            .values(raiz_id=nova_raiz_id)
            .execution_options(synchronize_session=False)
        )
        pasta.raiz_id = nova_raiz_id
    if era_raiz and destino_id is not None:
        # Passa a seguir os destinatários da nova raiz.
        _limpar_destinatarios(sessao, pasta)


def atualizar_pasta(
    sessao: Session, professor: Usuario, pasta_id: int, campos: dict
) -> Pasta:
    """Altera os campos presentes em `campos`. `pasta_pai_id` move a pasta (nulo
    leva para a raiz); `aluno_ids` e `grupo_ids` substituem os destinatários.

    Levanta PastaNaoEncontrada, PastaInvalida, NomeDePastaRepetido,
    AlunosInvalidos e GruposInvalidos, sem alterar nada.
    """
    _travar_arvore(sessao, professor.id)
    pasta = _pasta_do_professor(sessao, professor, pasta_id)
    movendo = "pasta_pai_id" in campos
    pai_final = campos.get("pasta_pai_id", pasta.pasta_pai_id)
    enviados = [campo for campo in DESTINATARIOS if campo in campos]
    if enviados and pai_final is not None:
        raise _destinatarios_so_na_raiz(enviados)

    aluno_ids = campos.get("aluno_ids")
    grupo_ids = campos.get("grupo_ids")
    if enviados:
        _conferir_destinatarios(
            todos_alunos=campos.get("todos_alunos", pasta.todos_alunos),
            todos_grupos=campos.get("todos_grupos", pasta.todos_grupos),
            aluno_ids=aluno_ids
            if aluno_ids is not None
            else sessao.scalars(
                select(PastaAluno.aluno_id).where(PastaAluno.pasta_id == pasta.id)
            ).all(),
            grupo_ids=grupo_ids
            if grupo_ids is not None
            else sessao.scalars(
                select(PastaGrupo.grupo_id).where(PastaGrupo.pasta_id == pasta.id)
            ).all(),
        )
        if aluno_ids is not None:
            validar_alunos(sessao, aluno_ids)
        if grupo_ids is not None:
            validar_grupos(sessao, professor, grupo_ids)
    if "nome" in campos or movendo:
        _conferir_nome(
            sessao, professor, campos.get("nome", pasta.nome), pai_final, pasta.id
        )

    if movendo and campos["pasta_pai_id"] != pasta.pasta_pai_id:
        _mover(sessao, professor, pasta, campos["pasta_pai_id"])
    if "nome" in campos:
        pasta.nome = campos["nome"]
    for campo in ("todos_alunos", "todos_grupos"):
        if campo in campos:
            setattr(pasta, campo, campos[campo])
    if aluno_ids is not None:
        sessao.execute(delete(PastaAluno).where(PastaAluno.pasta_id == pasta.id))
        _vincular(sessao, pasta, aluno_ids, ())
    if grupo_ids is not None:
        sessao.execute(delete(PastaGrupo).where(PastaGrupo.pasta_id == pasta.id))
        _vincular(sessao, pasta, (), grupo_ids)
    _gravar(sessao)
    sessao.commit()
    return pasta


def excluir_pasta(sessao: Session, professor: Usuario, pasta_id: int) -> None:
    """Soft delete da pasta e de tudo abaixo dela; os materiais vão para a
    limpeza do Drive.

    Levanta PastaNaoEncontrada.
    """
    _travar_arvore(sessao, professor.id)
    pasta = _pasta_do_professor(sessao, professor, pasta_id)
    subarvore = sessao.scalars(select(_descendentes(pasta.id).c.id)).all()
    arquivo_ids = sessao.scalars(
        select(AnexoPasta.arquivo_id).where(AnexoPasta.pasta_id.in_(subarvore))
    ).all()
    sessao.execute(
        update(Pasta)
        .where(Pasta.id.in_(subarvore))
        .values(deletado_em=agora())
        .execution_options(synchronize_session=False)
    )
    arquivo_service.marcar_para_remover(sessao, arquivo_ids)
    sessao.commit()


# --- materiais da pasta ---


def adicionar_arquivos(
    sessao: Session, professor: Usuario, pasta_id: int, arquivo_ids: Sequence[int]
) -> Pasta:
    """Guarda na pasta arquivos já enviados e confirmados pelo professor.

    Levanta PastaNaoEncontrada e ArquivosInvalidos, sem alterar nada.
    """
    # Sem a trava, uma exclusão simultânea deixaria o arquivo preso a uma pasta
    # excluída, fora do alcance da limpeza do Drive.
    _travar_arvore(sessao, professor.id)
    pasta = _pasta_do_professor(sessao, professor, pasta_id)
    arquivo_service.validar_para_vincular(sessao, professor, arquivo_ids)
    sessao.execute(
        insert(AnexoPasta).values(
            [{"pasta_id": pasta.id, "arquivo_id": item} for item in arquivo_ids]
        )
    )
    sessao.commit()
    return pasta


def _anexo(sessao: Session, pasta: Pasta, arquivo_id: int) -> AnexoPasta:
    anexo = sessao.get(AnexoPasta, arquivo_id)
    if anexo is None or anexo.pasta_id != pasta.id:
        raise ArquivoForaDaPasta
    return anexo


def remover_arquivo(
    sessao: Session, professor: Usuario, pasta_id: int, arquivo_id: int
) -> None:
    """Tira o material da pasta e o manda para a limpeza do Drive.

    Levanta PastaNaoEncontrada e ArquivoForaDaPasta.
    """
    pasta = _pasta_do_professor(sessao, professor, pasta_id)
    anexo = _anexo(sessao, pasta, arquivo_id)
    sessao.delete(anexo)
    arquivo_service.marcar_para_remover(sessao, [arquivo_id])
    sessao.commit()


def mover_arquivo(
    sessao: Session,
    professor: Usuario,
    pasta_id: int,
    arquivo_id: int,
    destino_id: int,
) -> Pasta:
    """Levanta PastaNaoEncontrada, ArquivoForaDaPasta e PastaInvalida."""
    _travar_arvore(sessao, professor.id)
    pasta = _pasta_do_professor(sessao, professor, pasta_id)
    anexo = _anexo(sessao, pasta, arquivo_id)
    destino = _pasta_de_destino(sessao, professor, destino_id, "pasta_id")
    anexo.pasta_id = destino.id
    sessao.commit()
    return destino


# --- materiais do aluno ---


def _visivel_para(aluno_id: int, raiz) -> ColumnElement[bool]:
    """Se a raiz (correlacionada na consulta externa) libera a árvore ao aluno."""
    em_grupo_ativo = and_(
        GrupoAluno.grupo_id == Grupo.id,
        GrupoAluno.aluno_id == aluno_id,
        Grupo.deletado_em.is_(None),
    )
    return or_(
        raiz.todos_alunos,
        and_(
            raiz.todos_grupos,
            exists().where(em_grupo_ativo, Grupo.professor_id == raiz.professor_id),
        ),
        exists().where(PastaAluno.pasta_id == raiz.id, PastaAluno.aluno_id == aluno_id),
        exists().where(
            PastaGrupo.pasta_id == raiz.id,
            PastaGrupo.grupo_id == Grupo.id,
            em_grupo_ativo,
        ),
    )


def _consulta_do_aluno(aluno: Usuario):
    raiz = aliased(Pasta)
    return (
        select(Pasta.id, Pasta.nome, Usuario.nome_completo.label("professor_nome"))
        .join(raiz, raiz.id == Pasta.raiz_id)
        .join(Usuario, Usuario.id == Pasta.professor_id)
        .where(
            Pasta.deletado_em.is_(None),
            raiz.deletado_em.is_(None),
            Usuario.deletado_em.is_(None),
            _visivel_para(aluno.id, raiz),
        )
    )


def listar_materiais(
    sessao: Session, aluno: Usuario, *, pagina: int, tamanho: int
) -> tuple[Sequence[Row], int]:
    """Pastas raiz liberadas ao aluno, em ordem alfabética, e o total."""
    consulta = _consulta_do_aluno(aluno).where(Pasta.pasta_pai_id.is_(None))
    total = sessao.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = sessao.execute(
        consulta.add_columns(*_totais())
        .order_by(*ORDEM_DAS_PASTAS)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_material(sessao: Session, aluno: Usuario, pasta_id: int) -> tuple[Pasta, str]:
    """Devolve a pasta e o nome do professor.

    Levanta PastaNaoEncontrada também quando a pasta não é liberada ao aluno.
    """
    linha = sessao.execute(
        _consulta_do_aluno(aluno).add_columns(Pasta).where(Pasta.id == pasta_id)
    ).first()
    if linha is None:
        raise PastaNaoEncontrada
    return linha.Pasta, linha.professor_nome

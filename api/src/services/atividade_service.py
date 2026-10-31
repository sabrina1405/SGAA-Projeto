"""Atividades: o professor cria e acompanha, o aluno responde. Os destinatários
são dinâmicos, como nos recados, e os arquivos sobem antes, por `arquivo_service`."""

from collections.abc import Sequence
from datetime import datetime, time, timedelta

from sqlalchemy import (
    ColumnElement,
    Row,
    and_,
    delete,
    exists,
    func,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.security import agora
from src.models.arquivo import Arquivo, StatusArquivo
from src.models.atividade import (
    AnexoAtividade,
    AnexoEntrega,
    Atividade,
    AtividadeAluno,
    AtividadeGrupo,
    EntregaAtividade,
    StatusEntrega,
)
from src.models.grupo import Grupo, GrupoAluno
from src.models.notificacao import TipoNotificacao
from src.models.usuario import Usuario
from src.schemas.aluno import HORARIO_DE_BRASILIA
from src.schemas.atividade import (
    SituacaoAtividade,
    SituacaoEntrega,
    SituacaoMinhaAtividade,
)
from src.services import arquivo_service, notificacao_service
from src.services.aula_service import formatar_horario
from src.services.grupo_service import validar_grupos
from src.services.usuario_service import (
    ORDEM_DOS_ALUNOS,
    consulta_alunos,
    validar_alunos,
)

HORA_DO_AVISO_DO_DIA = time(7, tzinfo=HORARIO_DE_BRASILIA)
TIPOS_DE_LEMBRETE = (
    TipoNotificacao.ATIVIDADE_LEMBRETE_SEMANA,
    TipoNotificacao.ATIVIDADE_LEMBRETE_DIA,
    TipoNotificacao.ATIVIDADE_VENCE_HOJE,
)


class AtividadeNaoEncontrada(Exception):
    pass


class EntregaNaoEncontrada(Exception):
    pass


class EntregaEncerrada(Exception):
    """A atividade venceu: quem já entregou não edita mais."""


class AtividadeInvalida(Exception):
    """Regra que depende da atividade inteira, e não de um campo só."""

    def __init__(self, tipo: str, mensagem: str, campos: list[str]) -> None:
        super().__init__(mensagem)
        self.tipo = tipo
        self.mensagem = mensagem
        self.campos = campos


# --- regras comuns ---


def _atividade_do_professor(
    sessao: Session, professor: Usuario, atividade_id: int
) -> Atividade:
    atividade = sessao.get(Atividade, atividade_id)
    if (
        atividade is None
        or atividade.deletado_em is not None
        or atividade.professor_id != professor.id
    ):
        raise AtividadeNaoEncontrada
    return atividade


def _conferir_periodo(liberar_em: datetime, vence_em: datetime) -> None:
    if vence_em <= liberar_em:
        raise AtividadeInvalida(
            "periodo_invalido",
            "o vencimento precisa ser depois da liberação",
            ["vence_em"],
        )


def _conferir_vencimento_futuro(vence_em: datetime) -> None:
    if vence_em <= agora():
        raise AtividadeInvalida(
            "periodo_invalido", "o vencimento precisa estar no futuro", ["vence_em"]
        )


def _conferir_destinatarios(
    *,
    todos_alunos: bool,
    todos_grupos: bool,
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> None:
    if todos_alunos and aluno_ids:
        raise AtividadeInvalida(
            "destinatarios_conflitantes",
            "com todos os alunos marcados, não informe alunos avulsos",
            ["aluno_ids"],
        )
    if todos_grupos and grupo_ids:
        raise AtividadeInvalida(
            "destinatarios_conflitantes",
            "com todos os grupos marcados, não informe grupos avulsos",
            ["grupo_ids"],
        )
    if not (todos_alunos or todos_grupos or aluno_ids or grupo_ids):
        raise AtividadeInvalida(
            "sem_destinatario",
            "informe ao menos um aluno ou grupo destinatário",
            ["aluno_ids", "grupo_ids"],
        )


def _vincular_destinatarios(
    sessao: Session,
    atividade: Atividade,
    aluno_ids: Sequence[int],
    grupo_ids: Sequence[int],
) -> None:
    if aluno_ids:
        sessao.execute(
            insert(AtividadeAluno)
            .values(
                [
                    {"atividade_id": atividade.id, "aluno_id": aluno_id}
                    for aluno_id in aluno_ids
                ]
            )
            .on_conflict_do_nothing()
        )
    if grupo_ids:
        sessao.execute(
            insert(AtividadeGrupo)
            .values(
                [
                    {"atividade_id": atividade.id, "grupo_id": grupo_id}
                    for grupo_id in grupo_ids
                ]
            )
            .on_conflict_do_nothing()
        )


def _destinado_a(aluno_id: int | ColumnElement[int]) -> ColumnElement[bool]:
    """Se a atividade (correlacionada na consulta externa) aparece para o aluno.

    `aluno_id` pode ser uma coluna, para buscar todos os alunos de uma atividade.
    """
    em_grupo_ativo = and_(
        GrupoAluno.grupo_id == Grupo.id,
        GrupoAluno.aluno_id == aluno_id,
        Grupo.deletado_em.is_(None),
    )
    return or_(
        Atividade.todos_alunos,
        and_(
            Atividade.todos_grupos,
            exists().where(
                em_grupo_ativo, Grupo.professor_id == Atividade.professor_id
            ),
        ),
        exists().where(
            AtividadeAluno.atividade_id == Atividade.id,
            AtividadeAluno.aluno_id == aluno_id,
        ),
        exists().where(
            AtividadeGrupo.atividade_id == Atividade.id,
            AtividadeGrupo.grupo_id == Grupo.id,
            em_grupo_ativo,
        ),
    )


def _momentos_dos_lembretes(
    liberar_em: datetime, vence_em: datetime
) -> dict[TipoNotificacao, datetime]:
    """Só os que caem no futuro, depois da liberação e antes do vencimento."""
    dia_do_vencimento = vence_em.astimezone(HORARIO_DE_BRASILIA).date()
    candidatos = {
        TipoNotificacao.ATIVIDADE_LEMBRETE_SEMANA: vence_em - timedelta(weeks=1),
        TipoNotificacao.ATIVIDADE_LEMBRETE_DIA: vence_em - timedelta(days=1),
        TipoNotificacao.ATIVIDADE_VENCE_HOJE: datetime.combine(
            dia_do_vencimento, HORA_DO_AVISO_DO_DIA
        ),
    }
    momento = agora()
    return {
        tipo: enviar_em
        for tipo, enviar_em in candidatos.items()
        if enviar_em > momento and liberar_em <= enviar_em < vence_em
    }


def _agendar_lembretes(sessao: Session, atividade: Atividade) -> None:
    lembretes = _momentos_dos_lembretes(atividade.liberar_em, atividade.vence_em)
    for tipo, enviar_em in lembretes.items():
        notificacao_service.agendar(sessao, tipo, atividade.id, enviar_em)


def _cancelar_lembretes(sessao: Session, atividade: Atividade) -> None:
    for tipo in TIPOS_DE_LEMBRETE:
        notificacao_service.cancelar_pendentes(sessao, tipo, atividade.id)


def _arquivos(sessao: Session, tabela: type, condicao: ColumnElement[bool]) -> list:
    return sessao.scalars(
        select(Arquivo)
        .join(tabela, tabela.arquivo_id == Arquivo.id)
        .where(
            condicao,
            Arquivo.deletado_em.is_(None),
            Arquivo.status == StatusArquivo.CONFIRMADO,
        )
        .order_by(Arquivo.id)
    ).all()


def listar_anexos(sessao: Session, atividade: Atividade) -> list[Arquivo]:
    return _arquivos(
        sessao, AnexoAtividade, AnexoAtividade.atividade_id == atividade.id
    )


def listar_anexos_da_entrega(
    sessao: Session, entrega: EntregaAtividade
) -> list[Arquivo]:
    return _arquivos(sessao, AnexoEntrega, AnexoEntrega.entrega_id == entrega.id)


def _ids_vinculados(sessao: Session, atividade: Atividade) -> set[int]:
    return {arquivo.id for arquivo in listar_anexos(sessao, atividade)}


# --- atividades do professor ---


def criar_atividade(
    sessao: Session,
    professor: Usuario,
    *,
    titulo: str,
    descricao: str,
    liberar_em: datetime,
    vence_em: datetime,
    permite_envio_arquivo: bool = False,
    todos_alunos: bool = False,
    todos_grupos: bool = False,
    aluno_ids: Sequence[int] = (),
    grupo_ids: Sequence[int] = (),
    arquivo_ids: Sequence[int] = (),
) -> tuple[Atividade, int | None]:
    """Devolve a atividade e o id do aviso, quando ele já deve sair na hora.

    Levanta AtividadeInvalida, AlunosInvalidos, GruposInvalidos e ArquivosInvalidos,
    sem criar nada.
    """
    _conferir_periodo(liberar_em, vence_em)
    _conferir_vencimento_futuro(vence_em)
    _conferir_destinatarios(
        todos_alunos=todos_alunos,
        todos_grupos=todos_grupos,
        aluno_ids=aluno_ids,
        grupo_ids=grupo_ids,
    )
    validar_alunos(sessao, aluno_ids)
    validar_grupos(sessao, professor, grupo_ids)
    arquivo_service.validar_para_vincular(sessao, professor, arquivo_ids)

    atividade = Atividade(
        professor_id=professor.id,
        titulo=titulo,
        descricao=descricao,
        liberar_em=liberar_em,
        vence_em=vence_em,
        permite_envio_arquivo=permite_envio_arquivo,
        todos_alunos=todos_alunos,
        todos_grupos=todos_grupos,
    )
    sessao.add(atividade)
    sessao.flush()
    _vincular_destinatarios(sessao, atividade, aluno_ids, grupo_ids)
    _vincular_arquivos(
        sessao, AnexoAtividade, "atividade_id", atividade.id, arquivo_ids
    )
    momento = agora()
    notificacao = notificacao_service.agendar(
        sessao,
        TipoNotificacao.ATIVIDADE_NOVA,
        atividade.id,
        max(liberar_em, momento),
    )
    _agendar_lembretes(sessao, atividade)
    sessao.commit()
    return atividade, notificacao.id if liberar_em <= momento else None


def _vincular_arquivos(
    sessao: Session,
    tabela: type,
    coluna: str,
    dono_id: int,
    arquivo_ids: Sequence[int],
) -> None:
    if arquivo_ids:
        sessao.execute(
            insert(tabela).values(
                [{coluna: dono_id, "arquivo_id": item} for item in arquivo_ids]
            )
        )


def listar_atividades(
    sessao: Session,
    professor: Usuario,
    *,
    situacao: SituacaoAtividade | None = None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    """Página das atividades, da que vence antes à que vence depois, e o total."""
    filtros = [Atividade.professor_id == professor.id, Atividade.deletado_em.is_(None)]
    if situacao == SituacaoAtividade.PROXIMAS:
        filtros.append(Atividade.vence_em >= agora())
    elif situacao == SituacaoAtividade.VENCIDAS:
        filtros.append(Atividade.vence_em < agora())
    total_entregas = (
        select(func.count())
        .select_from(EntregaAtividade)
        .where(EntregaAtividade.atividade_id == Atividade.id)
        .correlate(Atividade)
        .scalar_subquery()
    )
    total = sessao.scalar(select(func.count()).select_from(Atividade).where(*filtros))
    itens = sessao.execute(
        select(
            Atividade.id,
            Atividade.titulo,
            Atividade.liberar_em,
            Atividade.vence_em,
            Atividade.permite_envio_arquivo,
            total_entregas.label("total_entregas"),
        )
        .where(*filtros)
        .order_by(Atividade.vence_em, Atividade.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_atividade(
    sessao: Session, professor: Usuario, atividade_id: int
) -> Atividade:
    """Levanta AtividadeNaoEncontrada."""
    return _atividade_do_professor(sessao, professor, atividade_id)


def listar_alunos_da_atividade(sessao: Session, atividade: Atividade) -> Sequence[Row]:
    return sessao.execute(
        consulta_alunos()
        .join(AtividadeAluno, AtividadeAluno.aluno_id == Usuario.id)
        .where(AtividadeAluno.atividade_id == atividade.id)
        .order_by(*ORDEM_DOS_ALUNOS)
    ).all()


def listar_grupos_da_atividade(sessao: Session, atividade: Atividade) -> Sequence[Row]:
    return sessao.execute(
        select(Grupo.id, Grupo.titulo)
        .join(AtividadeGrupo, AtividadeGrupo.grupo_id == Grupo.id)
        .where(AtividadeGrupo.atividade_id == atividade.id, Grupo.deletado_em.is_(None))
        .order_by(func.lower(func.unaccent(Grupo.titulo)), Grupo.id)
    ).all()


def atualizar_atividade(
    sessao: Session, professor: Usuario, atividade_id: int, campos: dict
) -> tuple[Atividade, int | None]:
    """Altera os campos presentes em `campos`. As listas enviadas substituem as
    atuais. Devolve a atividade e o id do aviso de edição, se ele deve sair.

    Levanta AtividadeNaoEncontrada, AtividadeInvalida, AlunosInvalidos,
    GruposInvalidos e ArquivosInvalidos, sem alterar nada.
    """
    atividade = _atividade_do_professor(sessao, professor, atividade_id)
    aluno_ids_enviados = campos.pop("aluno_ids", None)
    grupo_ids_enviados = campos.pop("grupo_ids", None)
    arquivo_ids_enviados = campos.pop("arquivo_ids", None)
    aluno_ids = aluno_ids_enviados
    if aluno_ids is None:
        aluno_ids = sessao.scalars(
            select(AtividadeAluno.aluno_id).where(
                AtividadeAluno.atividade_id == atividade.id
            )
        ).all()
    grupo_ids = grupo_ids_enviados
    if grupo_ids is None:
        grupo_ids = sessao.scalars(
            select(AtividadeGrupo.grupo_id).where(
                AtividadeGrupo.atividade_id == atividade.id
            )
        ).all()

    liberar_em = campos.get("liberar_em", atividade.liberar_em)
    vence_em = campos.get("vence_em", atividade.vence_em)
    _conferir_periodo(liberar_em, vence_em)
    muda_liberacao = liberar_em != atividade.liberar_em
    muda_vencimento = vence_em != atividade.vence_em
    if muda_vencimento:
        _conferir_vencimento_futuro(vence_em)
    _conferir_destinatarios(
        todos_alunos=campos.get("todos_alunos", atividade.todos_alunos),
        todos_grupos=campos.get("todos_grupos", atividade.todos_grupos),
        aluno_ids=aluno_ids,
        grupo_ids=grupo_ids,
    )
    if aluno_ids_enviados is not None:
        validar_alunos(sessao, aluno_ids_enviados)
    if grupo_ids_enviados is not None:
        validar_grupos(sessao, professor, grupo_ids_enviados)
    vinculados = _ids_vinculados(sessao, atividade)
    if arquivo_ids_enviados is not None:
        arquivo_service.validar_para_vincular(
            sessao, professor, arquivo_ids_enviados, ja_vinculados=list(vinculados)
        )

    muda_anexos = (
        arquivo_ids_enviados is not None and set(arquivo_ids_enviados) != vinculados
    )
    # Mudar os destinatários não avisa quem já estava neles.
    muda_conteudo = (
        muda_liberacao
        or muda_vencimento
        or muda_anexos
        or any(
            campo in campos and campos[campo] != getattr(atividade, campo)
            for campo in ("titulo", "descricao")
        )
    )
    momento = agora()
    ja_liberada = atividade.liberar_em <= momento and liberar_em <= momento

    for campo, valor in campos.items():
        setattr(atividade, campo, valor)
    if aluno_ids_enviados is not None:
        sessao.execute(
            delete(AtividadeAluno).where(AtividadeAluno.atividade_id == atividade.id)
        )
        _vincular_destinatarios(sessao, atividade, aluno_ids_enviados, ())
    if grupo_ids_enviados is not None:
        sessao.execute(
            delete(AtividadeGrupo).where(AtividadeGrupo.atividade_id == atividade.id)
        )
        _vincular_destinatarios(sessao, atividade, (), grupo_ids_enviados)
    if muda_anexos:
        sessao.execute(
            delete(AnexoAtividade).where(AnexoAtividade.atividade_id == atividade.id)
        )
        _vincular_arquivos(
            sessao, AnexoAtividade, "atividade_id", atividade.id, arquivo_ids_enviados
        )
        arquivo_service.marcar_para_remover(
            sessao, list(vinculados - set(arquivo_ids_enviados))
        )
    if muda_liberacao:
        # Só muda o que ainda não foi enviado: não avisa de novo como nova.
        notificacao_service.reagendar(
            sessao,
            TipoNotificacao.ATIVIDADE_NOVA,
            atividade.id,
            max(liberar_em, momento),
        )
    if muda_liberacao or muda_vencimento:
        _cancelar_lembretes(sessao, atividade)
        _agendar_lembretes(sessao, atividade)
    notificacao = None
    if ja_liberada and muda_conteudo:
        notificacao = notificacao_service.agendar(
            sessao, TipoNotificacao.ATIVIDADE_EDITADA, atividade.id, momento
        )
    sessao.commit()
    return atividade, notificacao.id if notificacao is not None else None


def excluir_atividade(sessao: Session, professor: Usuario, atividade_id: int) -> None:
    """Soft delete. Marca os arquivos dela e das entregas, para os links públicos
    não ficarem no ar, e cancela os avisos pendentes.

    Levanta AtividadeNaoEncontrada.
    """
    atividade = _atividade_do_professor(sessao, professor, atividade_id)
    arquivos_da_atividade = sessao.scalars(
        select(AnexoAtividade.arquivo_id).where(
            AnexoAtividade.atividade_id == atividade.id
        )
    ).all()
    arquivos_das_entregas = sessao.scalars(
        select(AnexoEntrega.arquivo_id)
        .join(EntregaAtividade, EntregaAtividade.id == AnexoEntrega.entrega_id)
        .where(EntregaAtividade.atividade_id == atividade.id)
    ).all()
    arquivo_service.marcar_para_remover(
        sessao, [*arquivos_da_atividade, *arquivos_das_entregas]
    )
    for tipo in (
        TipoNotificacao.ATIVIDADE_NOVA,
        TipoNotificacao.ATIVIDADE_EDITADA,
        *TIPOS_DE_LEMBRETE,
    ):
        notificacao_service.cancelar_pendentes(sessao, tipo, atividade.id)
    atividade.deletado_em = agora()
    sessao.commit()


def listar_entregas(
    sessao: Session,
    professor: Usuario,
    *,
    situacao: SituacaoEntrega | None = None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    """Uma linha por aluno e atividade, do vencimento mais próximo ao mais distante.

    Uma entrega continua aparecendo mesmo que o aluno tenha saído dos destinatários.
    """
    momento = agora()
    filtros = [
        Atividade.deletado_em.is_(None),
        or_(EntregaAtividade.id.is_not(None), _destinado_a(Usuario.id)),
    ]
    if situacao == SituacaoEntrega.ENTREGUES:
        filtros.append(EntregaAtividade.id.is_not(None))
    elif situacao == SituacaoEntrega.PROXIMAS:
        filtros += [EntregaAtividade.id.is_(None), Atividade.vence_em >= momento]
    elif situacao == SituacaoEntrega.VENCIDAS:
        filtros += [EntregaAtividade.id.is_(None), Atividade.vence_em < momento]
    linhas = (
        consulta_alunos()
        .join(Atividade, Atividade.professor_id == professor.id)
        .outerjoin(
            EntregaAtividade,
            and_(
                EntregaAtividade.atividade_id == Atividade.id,
                EntregaAtividade.aluno_id == Usuario.id,
            ),
        )
        .where(*filtros)
    )
    total = sessao.scalar(linhas.with_only_columns(func.count()))
    itens = sessao.execute(
        linhas.with_only_columns(
            Atividade.id.label("atividade_id"),
            Atividade.titulo,
            Atividade.vence_em,
            Usuario.id.label("aluno_id"),
            Usuario.nome_completo.label("aluno_nome"),
            EntregaAtividade.status,
            EntregaAtividade.enviada_em,
        )
        .order_by(Atividade.vence_em, Atividade.id, *ORDEM_DOS_ALUNOS)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_entrega(
    sessao: Session, professor: Usuario, atividade_id: int, aluno_id: int
) -> EntregaAtividade:
    """Levanta AtividadeNaoEncontrada e EntregaNaoEncontrada."""
    atividade = _atividade_do_professor(sessao, professor, atividade_id)
    entrega = _entrega_do_aluno(sessao, atividade.id, aluno_id)
    if entrega is None:
        raise EntregaNaoEncontrada
    return entrega


# --- atividades do aluno ---


def _entrega_do_aluno(
    sessao: Session, atividade_id: int, aluno_id: int
) -> EntregaAtividade | None:
    return sessao.scalar(
        select(EntregaAtividade).where(
            EntregaAtividade.atividade_id == atividade_id,
            EntregaAtividade.aluno_id == aluno_id,
            EntregaAtividade.deletado_em.is_(None),
        )
    )


def _visivel_para(aluno: Usuario) -> list[ColumnElement[bool]]:
    return [
        Atividade.deletado_em.is_(None),
        Usuario.deletado_em.is_(None),
        Atividade.liberar_em <= agora(),
        or_(EntregaAtividade.id.is_not(None), _destinado_a(aluno.id)),
    ]


def _consulta_do_aluno(aluno: Usuario):
    return (
        select()
        .select_from(Atividade)
        .join(Usuario, Usuario.id == Atividade.professor_id)
        .outerjoin(
            EntregaAtividade,
            and_(
                EntregaAtividade.atividade_id == Atividade.id,
                EntregaAtividade.aluno_id == aluno.id,
            ),
        )
        .where(*_visivel_para(aluno))
    )


def listar_minhas_atividades(
    sessao: Session,
    aluno: Usuario,
    *,
    situacao: SituacaoMinhaAtividade | None = None,
    pagina: int,
    tamanho: int,
) -> tuple[Sequence[Row], int]:
    """Atividades liberadas para o aluno, do vencimento mais próximo ao mais
    distante, e o total sem paginar."""
    momento = agora()
    consulta = _consulta_do_aluno(aluno)
    if situacao == SituacaoMinhaAtividade.REALIZADAS:
        consulta = consulta.where(EntregaAtividade.id.is_not(None))
    elif situacao == SituacaoMinhaAtividade.PROXIMAS:
        consulta = consulta.where(
            EntregaAtividade.id.is_(None), Atividade.vence_em >= momento
        )
    elif situacao == SituacaoMinhaAtividade.VENCIDAS:
        consulta = consulta.where(
            EntregaAtividade.id.is_(None), Atividade.vence_em < momento
        )
    total = sessao.scalar(consulta.add_columns(func.count()))
    itens = sessao.execute(
        consulta.add_columns(
            Atividade.id,
            Atividade.titulo,
            Atividade.liberar_em,
            Atividade.vence_em,
            Atividade.permite_envio_arquivo,
            Usuario.nome_completo.label("professor_nome"),
            EntregaAtividade.status,
            EntregaAtividade.enviada_em,
        )
        .order_by(Atividade.vence_em, Atividade.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return itens, total


def obter_minha_atividade(
    sessao: Session, aluno: Usuario, atividade_id: int
) -> tuple[Atividade, str, EntregaAtividade | None]:
    """Devolve a atividade, o nome do professor e a entrega do aluno.

    Levanta AtividadeNaoEncontrada: também antes da liberação ou sem ser destinatário.
    """
    linha = sessao.execute(
        _consulta_do_aluno(aluno)
        .add_columns(Atividade, Usuario.nome_completo)
        .where(Atividade.id == atividade_id)
    ).first()
    if linha is None:
        raise AtividadeNaoEncontrada
    atividade, professor_nome = linha
    return atividade, professor_nome, _entrega_do_aluno(sessao, atividade.id, aluno.id)


def _atualizar_anexos_da_entrega(
    sessao: Session,
    entrega: EntregaAtividade,
    vinculados: set[int],
    arquivo_ids: Sequence[int],
) -> None:
    sessao.execute(delete(AnexoEntrega).where(AnexoEntrega.entrega_id == entrega.id))
    _vincular_arquivos(sessao, AnexoEntrega, "entrega_id", entrega.id, arquivo_ids)
    arquivo_service.marcar_para_remover(sessao, list(vinculados - set(arquivo_ids)))


def salvar_entrega(
    sessao: Session,
    aluno: Usuario,
    atividade_id: int,
    *,
    resposta: str,
    arquivo_ids: Sequence[int] | None = None,
) -> EntregaAtividade:
    """Cria ou edita a resposta do aluno. Criada depois do vencimento, fica como
    atrasada; a edição só vale até o vencimento.

    Levanta AtividadeNaoEncontrada, AtividadeInvalida, ArquivosInvalidos e
    EntregaEncerrada, sem alterar nada.
    """
    atividade, _, entrega = obter_minha_atividade(sessao, aluno, atividade_id)
    if arquivo_ids and not atividade.permite_envio_arquivo:
        raise AtividadeInvalida(
            "envio_de_arquivo_desligado",
            "esta atividade não aceita arquivos",
            ["arquivo_ids"],
        )
    momento = agora()
    vencida = momento > atividade.vence_em
    if entrega is not None and vencida:
        raise EntregaEncerrada
    vinculados = (
        {arquivo.id for arquivo in listar_anexos_da_entrega(sessao, entrega)}
        if entrega is not None
        else set()
    )
    if arquivo_ids is not None:
        arquivo_service.validar_para_vincular(
            sessao, aluno, arquivo_ids, ja_vinculados=list(vinculados)
        )
    if entrega is None:
        # Dois toques em "Enviar" ao mesmo tempo não criam duas entregas.
        sessao.execute(
            insert(EntregaAtividade)
            .values(
                atividade_id=atividade.id,
                aluno_id=aluno.id,
                resposta=resposta,
                status=(
                    StatusEntrega.ENTREGUE_COM_ATRASO
                    if vencida
                    else StatusEntrega.ENVIADO
                ),
                enviada_em=momento,
            )
            .on_conflict_do_nothing(constraint="uq_entrega_atividade_atividade_aluno")
        )
        entrega = _entrega_do_aluno(sessao, atividade.id, aluno.id)
    entrega.resposta = resposta
    entrega.enviada_em = momento
    if arquivo_ids is not None:
        _atualizar_anexos_da_entrega(sessao, entrega, vinculados, arquivo_ids)
    sessao.commit()
    return entrega


# --- notificações push ---

_TITULOS: dict[TipoNotificacao, str] = {
    TipoNotificacao.ATIVIDADE_NOVA: "Nova atividade",
    TipoNotificacao.ATIVIDADE_EDITADA: "Atividade alterada",
    TipoNotificacao.ATIVIDADE_LEMBRETE_SEMANA: "Atividade vence em 1 semana",
    TipoNotificacao.ATIVIDADE_LEMBRETE_DIA: "Atividade vence amanhã",
    TipoNotificacao.ATIVIDADE_VENCE_HOJE: "Atividade vence hoje",
}


def _resolvedor(tipo: TipoNotificacao) -> notificacao_service.Resolvedor:
    def resolver(
        sessao: Session, atividade_id: int
    ) -> notificacao_service.Conteudo | None:
        atividade = sessao.get(Atividade, atividade_id)
        momento = agora()
        if (
            atividade is None
            or atividade.deletado_em is not None
            or atividade.liberar_em > momento
        ):
            return None
        lembrete = tipo in TIPOS_DE_LEMBRETE
        # Cobre uma nova tentativa que só saiu depois do vencimento.
        if lembrete and atividade.vence_em <= momento:
            return None
        professor = sessao.get(Usuario, atividade.professor_id)
        if professor is None or professor.deletado_em is not None:
            return None
        destinatarios = (
            consulta_alunos()
            .with_only_columns(Usuario.id)
            .join(Atividade, Atividade.id == atividade.id)
            .where(_destinado_a(Usuario.id))
        )
        if lembrete:
            destinatarios = destinatarios.where(
                ~exists().where(
                    EntregaAtividade.atividade_id == atividade.id,
                    EntregaAtividade.aluno_id == Usuario.id,
                )
            )
        return notificacao_service.Conteudo(
            usuario_ids=sessao.scalars(destinatarios).all(),
            titulo=f"{_TITULOS[tipo]}: {atividade.titulo}",
            corpo=(
                f"Entrega até {formatar_horario(atividade.vence_em)}, "
                f"com {professor.nome_completo}"
            ),
            dados={"tipo": tipo.value, "atividade_id": atividade.id},
        )

    return resolver


RESOLVEDORES: dict[TipoNotificacao, notificacao_service.Resolvedor] = {
    tipo: _resolvedor(tipo) for tipo in _TITULOS
}

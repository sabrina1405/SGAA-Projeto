"""Arquivos no Drive. Sobem antes de salvar o formulário: a atividade ou a entrega
recebe os ids depois. O que fica sem vínculo é apagado pela tarefa agendada."""

import logging
from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import ColumnElement, and_, exists, func, or_, select, update
from sqlalchemy.orm import Session

from src.core.drive import ArmazenamentoDrive, FalhaDrive
from src.core.security import agora
from src.models.arquivo import Arquivo, StatusArquivo
from src.models.atividade import AnexoAtividade, AnexoEntrega
from src.models.usuario import Usuario

logger = logging.getLogger(__name__)

TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024
# Sem HTML nem SVG, que rodariam script no navegador de quem abre o link.
TIPOS_PERMITIDOS = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)
# Evita que um usuário ocupe o espaço do Drive com arquivos que nunca vincula.
MAXIMO_SEM_VINCULO_POR_USUARIO = 10
VALIDADE_DO_PENDENTE = timedelta(hours=1)
VALIDADE_SEM_VINCULO = timedelta(hours=24)
REMOCOES_POR_EXECUCAO = 20


class ArquivoNaoEncontrado(Exception):
    pass


class ArquivoEmUso(Exception):
    pass


class LimiteDeArquivos(Exception):
    pass


class ArquivoInvalido(Exception):
    def __init__(self, tipo: str, mensagem: str, campos: list[str]) -> None:
        super().__init__(mensagem)
        self.tipo = tipo
        self.mensagem = mensagem
        self.campos = campos


class ArquivosInvalidos(Exception):
    def __init__(self, ids: list[int]) -> None:
        super().__init__(ids)
        self.ids = ids


def _sem_vinculo() -> ColumnElement[bool]:
    return and_(
        ~exists().where(AnexoAtividade.arquivo_id == Arquivo.id),
        ~exists().where(AnexoEntrega.arquivo_id == Arquivo.id),
    )


def _do_usuario(sessao: Session, usuario: Usuario, arquivo_id: int) -> Arquivo:
    arquivo = sessao.get(Arquivo, arquivo_id, with_for_update=True)
    if (
        arquivo is None
        or arquivo.deletado_em is not None
        or arquivo.enviado_por_id != usuario.id
        or arquivo.status == StatusArquivo.REMOVER
    ):
        raise ArquivoNaoEncontrado
    return arquivo


def _conferir_tipo_e_tamanho(tipo_mime: str, tamanho: int) -> None:
    if tipo_mime not in TIPOS_PERMITIDOS:
        raise ArquivoInvalido(
            "tipo_nao_permitido", "este tipo de arquivo não é aceito", ["tipo_mime"]
        )
    if tamanho > TAMANHO_MAXIMO_BYTES:
        raise ArquivoInvalido(
            "arquivo_muito_grande", "o arquivo pode ter no máximo 5 MB", ["tamanho"]
        )


def abrir_sessao(
    sessao: Session,
    usuario: Usuario,
    drive: ArmazenamentoDrive,
    *,
    nome: str,
    tipo_mime: str,
    tamanho: int,
    origem: str | None = None,
) -> tuple[Arquivo, str]:
    """Devolve o arquivo e a URL para onde o app envia o conteúdo.

    Levanta ArquivoInvalido, LimiteDeArquivos e FalhaDrive, sem gravar nada.
    """
    _conferir_tipo_e_tamanho(tipo_mime, tamanho)
    sem_vinculo = sessao.scalar(
        select(func.count())
        .select_from(Arquivo)
        .where(
            Arquivo.enviado_por_id == usuario.id,
            Arquivo.deletado_em.is_(None),
            Arquivo.status != StatusArquivo.REMOVER,
            _sem_vinculo(),
        )
    )
    if sem_vinculo >= MAXIMO_SEM_VINCULO_POR_USUARIO:
        raise LimiteDeArquivos
    arquivo = Arquivo(
        enviado_por_id=usuario.id, nome=nome, tipo_mime=tipo_mime, tamanho=tamanho
    )
    sessao.add(arquivo)
    sessao.flush()
    try:
        url = drive.abrir_sessao(
            arquivo_id=arquivo.id,
            nome=nome,
            tipo_mime=tipo_mime,
            tamanho=tamanho,
            origem=origem,
        )
    except FalhaDrive:
        sessao.rollback()
        raise
    sessao.commit()
    return arquivo, url


def confirmar(
    sessao: Session,
    usuario: Usuario,
    drive: ArmazenamentoDrive,
    arquivo_id: int,
    drive_file_id: str,
) -> Arquivo:
    """Confere no Drive o que foi enviado e cria o link. Repetir é seguro, o que
    cobre o timeout de uma chamada anterior.

    Levanta ArquivoNaoEncontrado, ArquivoInvalido e FalhaDrive.
    """
    arquivo = _do_usuario(sessao, usuario, arquivo_id)
    if arquivo.status == StatusArquivo.CONFIRMADO:
        return arquivo
    no_drive = drive.obter_arquivo(drive_file_id)
    # O id vem do cliente: um arquivo de outra sessão não é confirmado nem apagado.
    if no_drive is None or no_drive.arquivo_id != str(arquivo.id):
        raise ArquivoInvalido(
            "arquivo_nao_enviado",
            "o arquivo não foi encontrado no Drive",
            ["drive_file_id"],
        )
    try:
        # O declarado na sessão não é garantia: vale o que está no Drive.
        _conferir_tipo_e_tamanho(no_drive.tipo_mime, no_drive.tamanho)
    except ArquivoInvalido:
        # A tarefa agendada apaga, para não gastar o tempo da requisição.
        arquivo.drive_file_id = no_drive.id
        arquivo.status = StatusArquivo.REMOVER
        sessao.commit()
        raise
    drive.compartilhar_por_link(no_drive.id)
    if not no_drive.url:
        raise FalhaDrive("o Drive não devolveu o link do arquivo")
    arquivo.drive_file_id = no_drive.id
    arquivo.drive_url = no_drive.url
    arquivo.tamanho = no_drive.tamanho
    arquivo.status = StatusArquivo.CONFIRMADO
    sessao.commit()
    return arquivo


def descartar(sessao: Session, usuario: Usuario, arquivo_id: int) -> None:
    """Desiste de um arquivo ainda sem vínculo.

    Levanta ArquivoNaoEncontrado e ArquivoEmUso.
    """
    arquivo = _do_usuario(sessao, usuario, arquivo_id)
    em_uso = sessao.scalar(
        select(~_sem_vinculo()).select_from(Arquivo).where(Arquivo.id == arquivo.id)
    )
    if em_uso:
        raise ArquivoEmUso
    arquivo.status = StatusArquivo.REMOVER
    sessao.commit()


def validar_para_vincular(
    sessao: Session,
    usuario: Usuario,
    arquivo_ids: Sequence[int],
    *,
    ja_vinculados: Sequence[int] = (),
) -> None:
    """Levanta ArquivosInvalidos com os ids que não são do usuário, não foram
    confirmados ou já estão vinculados a outra atividade ou entrega."""
    if not arquivo_ids:
        return
    validos = set(
        sessao.scalars(
            select(Arquivo.id).where(
                Arquivo.id.in_(arquivo_ids),
                Arquivo.enviado_por_id == usuario.id,
                Arquivo.deletado_em.is_(None),
                Arquivo.status == StatusArquivo.CONFIRMADO,
                or_(Arquivo.id.in_(ja_vinculados), _sem_vinculo()),
            )
        )
    )
    invalidos = [item for item in arquivo_ids if item not in validos]
    if invalidos:
        raise ArquivosInvalidos(invalidos)


def marcar_para_remover(sessao: Session, arquivo_ids: Sequence[int]) -> None:
    """Não faz commit: entra na transação da feature."""
    if arquivo_ids:
        sessao.execute(
            update(Arquivo)
            .where(Arquivo.id.in_(arquivo_ids))
            .values(status=StatusArquivo.REMOVER)
        )


def limpar(
    sessao: Session,
    drive: ArmazenamentoDrive,
    *,
    limite: int = REMOCOES_POR_EXECUCAO,
) -> int:
    """Apaga do Drive o que foi removido ou abandonado. Devolve quantos saíram.

    Para na primeira falha: com o Drive fora do ar, cada tentativa só gastaria o
    tempo da tarefa agendada. O que sobrou fica para a próxima execução.
    """
    momento = agora()
    arquivos = sessao.scalars(
        select(Arquivo)
        .where(
            Arquivo.deletado_em.is_(None),
            or_(
                Arquivo.status == StatusArquivo.REMOVER,
                and_(
                    Arquivo.status == StatusArquivo.PENDENTE,
                    Arquivo.criado_em <= momento - VALIDADE_DO_PENDENTE,
                ),
                and_(
                    Arquivo.status == StatusArquivo.CONFIRMADO,
                    Arquivo.criado_em <= momento - VALIDADE_SEM_VINCULO,
                    _sem_vinculo(),
                ),
            ),
        )
        .order_by(Arquivo.id)
        .limit(limite)
    ).all()
    removidos = 0
    for arquivo in arquivos:
        try:
            no_drive = (
                [arquivo.drive_file_id]
                if arquivo.drive_file_id
                else drive.buscar_por_arquivo_id(arquivo.id)
            )
            for drive_file_id in no_drive:
                drive.apagar(drive_file_id)
        except FalhaDrive:
            logger.exception("Falha ao apagar o arquivo %s do Drive", arquivo.id)
            break
        arquivo.deletado_em = agora()
        sessao.commit()
        removidos += 1
    return removidos


def limpar_sem_falhar(sessao: Session, drive: ArmazenamentoDrive) -> int:
    """Para a tarefa agendada: um erro aqui não afeta o push nem os recibos."""
    try:
        return limpar(sessao, drive)
    except Exception:
        logger.exception("Falha na limpeza dos arquivos")
        sessao.rollback()
        return 0

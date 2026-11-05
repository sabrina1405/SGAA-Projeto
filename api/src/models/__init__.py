from src.models.aluno import Aluno
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
from src.models.aula import Aula, AulaAluno, AulaGrupo, StatusAula, StatusParticipacao
from src.models.codigo_verificacao import CodigoVerificacao
from src.models.grupo import Grupo, GrupoAluno
from src.models.notificacao import (
    Dispositivo,
    EnvioPush,
    Notificacao,
    StatusEnvio,
    TipoNotificacao,
)
from src.models.professor import Professor
from src.models.recado import Recado, RecadoAluno, RecadoGeral, RecadoGrupo
from src.models.usuario import TipoUsuario, Usuario

__all__ = [
    "Aluno",
    "AnexoAtividade",
    "AnexoEntrega",
    "Arquivo",
    "Atividade",
    "AtividadeAluno",
    "AtividadeGrupo",
    "Aula",
    "AulaAluno",
    "AulaGrupo",
    "CodigoVerificacao",
    "Dispositivo",
    "EntregaAtividade",
    "EnvioPush",
    "Grupo",
    "GrupoAluno",
    "Notificacao",
    "Professor",
    "Recado",
    "RecadoAluno",
    "RecadoGeral",
    "RecadoGrupo",
    "StatusArquivo",
    "StatusAula",
    "StatusEntrega",
    "StatusEnvio",
    "StatusParticipacao",
    "TipoNotificacao",
    "TipoUsuario",
    "Usuario",
]

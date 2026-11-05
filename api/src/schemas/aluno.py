from datetime import date, datetime, timedelta, timezone
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from src.schemas.base import SchemaEntrada
from src.schemas.tipos import Cpf, NomeCompleto, NovaSenha, Telefone

MAIORIDADE = 18
IDADE_MAXIMA = 120
# O Brasil não tem horário de verão desde 2019.
HORARIO_DE_BRASILIA = timezone(timedelta(hours=-3))


def hoje() -> date:
    return datetime.now(HORARIO_DE_BRASILIA).date()


def calcular_idade(data_nascimento: date, referencia: date) -> int:
    ainda_nao_fez_aniversario = (referencia.month, referencia.day) < (
        data_nascimento.month,
        data_nascimento.day,
    )
    return referencia.year - data_nascimento.year - ainda_nao_fez_aniversario


class PrimeiroAcessoAlunoEntrada(SchemaEntrada):
    """Formulário de primeiro acesso do aluno.

    Para menor de idade, `cpf` e `telefone` são os do responsável e
    `responsavel_nome` é obrigatório. Para maior, são os do próprio aluno e
    `responsavel_nome` não deve ser enviado.
    """

    data_nascimento: date
    cpf: Cpf
    telefone: Telefone
    responsavel_nome: NomeCompleto | None = None
    nova_senha: NovaSenha

    @field_validator("data_nascimento")
    @classmethod
    def _data_plausivel(cls, valor: date) -> date:
        if valor >= hoje() or calcular_idade(valor, hoje()) > IDADE_MAXIMA:
            raise ValueError("data de nascimento inválida")
        return valor

    @model_validator(mode="after")
    def _responsavel_conforme_a_idade(self) -> Self:
        if self.possui_responsavel and self.responsavel_nome is None:
            raise ValueError("menor de idade deve informar o nome do responsável")
        if not self.possui_responsavel and self.responsavel_nome is not None:
            raise ValueError("maior de idade não deve informar responsável")
        return self

    @property
    def possui_responsavel(self) -> bool:
        return calcular_idade(self.data_nascimento, hoje()) < MAIORIDADE


class PerfilAlunoAtualizar(SchemaEntrada):
    """Edição do perfil pelo próprio aluno: só o que for enviado é alterado.

    Quem tem responsável edita os campos `responsavel_*`; quem não tem edita
    `telefone`. E-mail, CPF do aluno e data de nascimento não são editáveis.
    """

    nome_completo: NomeCompleto | None = None
    telefone: Telefone | None = None
    responsavel_nome: NomeCompleto | None = None
    responsavel_cpf: Cpf | None = None
    responsavel_telefone: Telefone | None = None

    @model_validator(mode="after")
    def _campos_enviados(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo")
        if any(getattr(self, campo) is None for campo in self.model_fields_set):
            raise ValueError("os campos enviados não podem ser nulos")
        return self


class AlunoListaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    email: str
    # Do responsável, quando o aluno tem um.
    telefone: str


class PerfilAlunoDados(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data_nascimento: date
    possui_responsavel: bool
    cpf: str | None
    telefone: str | None
    responsavel_nome: str | None
    responsavel_cpf: str | None
    responsavel_telefone: str | None


class PerfilAlunoResposta(BaseModel):
    id: int
    nome_completo: str
    email: str
    perfil: PerfilAlunoDados


class AlunoDetalheResposta(BaseModel):
    id: int
    nome_completo: str
    email: str
    primeiro_acesso_concluido: bool
    # Nulo enquanto o aluno não conclui o primeiro acesso.
    perfil: PerfilAlunoDados | None
    # Reservados: sempre vazios até existirem os módulos de aulas e pagamentos.
    aulas: list[dict[str, Any]] = []
    pagamentos: list[dict[str, Any]] = []

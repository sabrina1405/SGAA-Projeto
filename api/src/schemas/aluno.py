from datetime import date, datetime, timedelta, timezone
from typing import Self

from pydantic import field_validator, model_validator

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

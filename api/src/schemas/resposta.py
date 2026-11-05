from pydantic import BaseModel


class Resposta[T](BaseModel):
    """Envelope de toda resposta de sucesso."""

    sucesso: bool = True
    mensagem: str
    dados: T | None = None


class ErroCampo(BaseModel):
    local: list[str | int]
    tipo: str
    mensagem: str


class RespostaErro(BaseModel):
    """Envelope das respostas de erro, montado em `src.core.errors`."""

    sucesso: bool = False
    mensagem: str
    dados: None = None
    # Só nos erros de validação (422).
    erros: list[ErroCampo] | None = None

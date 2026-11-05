from pydantic import BaseModel, ConfigDict


class SchemaEntrada(BaseModel):
    """Base dos corpos de requisição: rejeita campos desconhecidos."""

    model_config = ConfigDict(extra="forbid", frozen=True)

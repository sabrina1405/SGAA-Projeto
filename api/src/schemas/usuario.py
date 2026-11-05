from pydantic import BaseModel, ConfigDict

from src.models.usuario import TipoUsuario
from src.schemas.base import SchemaEntrada
from src.schemas.tipos import Email, NomeCompleto


class AlunoCriar(SchemaEntrada):
    nome_completo: NomeCompleto
    email: Email


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    email: str
    tipo: TipoUsuario

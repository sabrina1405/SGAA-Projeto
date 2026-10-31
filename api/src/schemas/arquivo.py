from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import SchemaEntrada
from src.schemas.tipos import DriveFileId, NomeArquivo


class ArquivoSessaoCriar(SchemaEntrada):
    nome: NomeArquivo
    tipo_mime: str = Field(min_length=1, max_length=100)
    tamanho: int = Field(ge=1)


class ArquivoConfirmar(SchemaEntrada):
    drive_file_id: DriveFileId


class ArquivoSessaoResposta(BaseModel):
    arquivo_id: int
    url_upload: str


class ArquivoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo_mime: str
    tamanho: int
    url: str | None = Field(validation_alias="drive_url")

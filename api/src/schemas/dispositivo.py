from typing import Literal

from src.schemas.base import SchemaEntrada
from src.schemas.tipos import TokenPush


class DispositivoRegistrar(SchemaEntrada):
    token: TokenPush
    plataforma: Literal["android", "ios"] | None = None

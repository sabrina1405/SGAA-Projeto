from pydantic import BaseModel

TAMANHO_PADRAO = 20
TAMANHO_MAXIMO = 100
# Com 100 itens por página, cobre 50 mil registros.
PAGINA_MAXIMA = 500


class Pagina[T](BaseModel):
    itens: list[T]
    total: int

import os

from fastapi import APIRouter, FastAPI

from src.api.routes import (
    agenda,
    arquivos,
    atividades,
    aulas,
    auth,
    dispositivos,
    grupos,
    minhas_atividades,
    mural,
    recados,
    usuarios,
)
from src.core.errors import registrar_tratadores
from src.schemas.resposta import RespostaErro


def rotas_da_documentacao(ambiente: str | None) -> dict[str, None]:
    """Em produção, /docs, /redoc e /openapi.json não são publicados."""
    if ambiente == "prod":
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {}


app = FastAPI(
    title="SGAA API",
    description="Backend do Sistema de Gerenciamento de Alunos e Aulas",
    version="0.1.0",
    **rotas_da_documentacao(os.getenv("AMBIENTE")),
)
registrar_tratadores(app)

# Uma mudança incompatível em um recurso entra em um router /v2, sem tirar este do ar.
v1 = APIRouter(prefix="/v1", responses={422: {"model": RespostaErro}})
v1.include_router(auth.router)
v1.include_router(usuarios.router)
v1.include_router(grupos.router)
v1.include_router(recados.router)
v1.include_router(mural.router)
v1.include_router(aulas.router)
v1.include_router(agenda.router)
v1.include_router(arquivos.router)
v1.include_router(atividades.router)
v1.include_router(minhas_atividades.router)
v1.include_router(dispositivos.router)
app.include_router(v1)


@app.get("/")
async def root():
    return {"message": "Hello World"}

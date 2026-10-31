from fastapi import APIRouter, FastAPI

from src.api.routes import auth, grupos, usuarios
from src.core.errors import registrar_tratadores
from src.schemas.resposta import RespostaErro

app = FastAPI(
    title="SGAA API",
    description="Backend do Sistema de Gerenciamento de Alunos e Aulas",
    version="0.1.0",
)
registrar_tratadores(app)

# Uma mudança incompatível em um recurso entra em um router /v2, sem tirar este do ar.
v1 = APIRouter(prefix="/v1", responses={422: {"model": RespostaErro}})
v1.include_router(auth.router)
v1.include_router(usuarios.router)
v1.include_router(grupos.router)
app.include_router(v1)


@app.get("/")
async def root():
    return {"message": "Hello World"}

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from src.api.routes import auth, usuarios
from src.core.errors import tratar_erro_validacao

app = FastAPI(
    title="SGAA API",
    description="Backend do Sistema de Gerenciamento de Alunos e Aulas",
    version="0.1.0",
)
app.add_exception_handler(RequestValidationError, tratar_erro_validacao)
app.include_router(auth.router)
app.include_router(usuarios.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

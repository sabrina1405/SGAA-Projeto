from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def tratar_erro_validacao(
    _: Request, erro: RequestValidationError
) -> JSONResponse:
    # O handler padrão do FastAPI devolve o valor recebido em "input" (e às vezes
    # em "ctx"), o que ecoaria senhas e códigos na resposta de erro.
    erros = [
        {"type": item["type"], "loc": item["loc"], "msg": item["msg"]}
        for item in erro.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(erros)})

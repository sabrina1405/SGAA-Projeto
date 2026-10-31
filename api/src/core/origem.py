import hmac

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

CABECALHO_DA_ORIGEM = b"x-origem-cloudfront"


class ExigirCloudFront:
    """Recusa com 403 a requisição que não veio pelo CloudFront.

    O CloudFront envia o cabeçalho com o segredo do ambiente. Sem ele, quem
    chamasse a Function URL direto escaparia do rate limit do WAF.
    """

    def __init__(self, app: ASGIApp, segredo: str) -> None:
        self.app = app
        self.segredo = segredo.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            recebido = dict(scope["headers"]).get(CABECALHO_DA_ORIGEM, b"")
            if not hmac.compare_digest(recebido, self.segredo):
                resposta = JSONResponse(
                    status_code=403,
                    content={
                        "sucesso": False,
                        "mensagem": "Acesso não permitido",
                        "dados": None,
                    },
                )
                await resposta(scope, receive, send)
                return
        await self.app(scope, receive, send)

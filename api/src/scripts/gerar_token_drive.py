"""Gera o refresh token do Google Drive. Rode só depois de publicar o app OAuth:
em modo de teste, o token expira em 7 dias. Ver docs/google_drive.md.

Uso: poetry run python -m src.scripts.gerar_token_drive
"""

import http.server
import json
import secrets
import sys
import urllib.parse
import urllib.request
from getpass import getpass

URL_AUTORIZACAO = "https://accounts.google.com/o/oauth2/v2/auth"
URL_TOKEN = "https://oauth2.googleapis.com/token"
ESCOPO = "https://www.googleapis.com/auth/drive.file"


def _esperar_o_codigo(estado_esperado: str, servidor: http.server.HTTPServer) -> str:
    resultado: dict[str, str] = {}

    class Tratador(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            consulta = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if consulta.get("state") == [estado_esperado] and "code" in consulta:
                resultado["codigo"] = consulta["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Pode fechar esta aba e voltar ao terminal.")

        def log_message(self, *_: object) -> None:
            pass

    servidor.RequestHandlerClass = Tratador
    servidor.handle_request()
    if "codigo" not in resultado:
        sys.exit("A autorização não foi concluída.")
    return resultado["codigo"]


def main() -> None:
    client_id = input("Client ID: ").strip()
    client_secret = getpass("Client secret (não aparece na tela): ").strip()
    servidor = http.server.HTTPServer(
        ("127.0.0.1", 0), http.server.BaseHTTPRequestHandler
    )
    redirect_uri = f"http://127.0.0.1:{servidor.server_address[1]}"
    estado = secrets.token_urlsafe(24)
    consulta = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": ESCOPO,
            # Sem estes dois, o Google pode não devolver o refresh token.
            "access_type": "offline",
            "prompt": "consent",
            "state": estado,
        }
    )
    print(
        "\nAbra este link logado na conta do projeto e autorize:\n"
        f"\n{URL_AUTORIZACAO}?{consulta}\n"
    )
    codigo = _esperar_o_codigo(estado, servidor)
    corpo = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": codigo,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode()
    with urllib.request.urlopen(
        urllib.request.Request(URL_TOKEN, data=corpo, method="POST"), timeout=30
    ) as resposta:
        refresh_token = json.loads(resposta.read()).get("refresh_token")
    if not refresh_token:
        sys.exit("O Google não devolveu o refresh token. Revogue o acesso e repita.")
    print(
        "\nGuarde como GOOGLE_DRIVE_REFRESH_TOKEN (SecureString no Parameter Store). "
        f"Não faça commit:\n\n{refresh_token}\n"
    )


if __name__ == "__main__":
    main()

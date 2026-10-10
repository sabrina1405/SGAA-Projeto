"""Cria a conta da professora. Uso: poetry run python -m src.scripts.criar_professor"""

import os
import secrets
import sys
from getpass import getpass

from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from src.core.config import obter_config
from src.core.database import obter_engine
from src.core.security import hash_senha
from src.models.usuario import TipoUsuario
from src.schemas.tipos import Email, NomeCompleto, NovaSenha
from src.services.usuario_service import EmailJaCadastrado, criar_usuario


def _normalizar_url(url: str) -> str | None:
    # O Supabase entrega postgresql:// (ou postgres://); o projeto usa o psycopg.
    if url.startswith("postgresql+psycopg://"):
        return url
    for prefixo in ("postgresql://", "postgres://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url.removeprefix(prefixo)
    return None


def _escolher_banco() -> bool:
    """Define o banco de destino. Devolve False se a execução deve parar."""
    print("Onde a conta será criada?")
    print("  1) Banco local (usa o DATABASE_URL do .env)")
    print("  2) Homologação ou produção (pede a URL do banco)")
    opcao = input("Opção [1]: ").strip() or "1"
    if opcao == "1":
        return True
    if opcao != "2":
        print("Opção inválida.")
        return False

    url = _normalizar_url(getpass("URL do banco (pooler do Supabase): ").strip())
    if url is None:
        print("A URL deve começar com postgresql://")
        return False
    destino = url.rsplit("@", 1)[-1]
    if input(f"Criar a conta em {destino}? Digite 'sim': ").strip() != "sim":
        print("Cancelado; nada foi criado.")
        return False

    # A variável de ambiente tem precedência sobre o .env e vale só neste processo.
    os.environ["DATABASE_URL"] = url
    # A chave não é usada na criação da conta, mas a configuração exige uma.
    os.environ.setdefault("SECRET_KEY", secrets.token_urlsafe(48))
    obter_config.cache_clear()
    obter_engine.cache_clear()
    return True


def main() -> int:
    if not _escolher_banco():
        return 1
    try:
        nome_completo = TypeAdapter(NomeCompleto).validate_python(
            input("Nome completo: ")
        )
        email = TypeAdapter(Email).validate_python(input("E-mail: "))
        senha = TypeAdapter(NovaSenha).validate_python(getpass("Senha: "))
    except ValidationError as erro:
        print("Dado inválido: " + "; ".join(item["msg"] for item in erro.errors()))
        return 1
    if getpass("Confirme a senha: ") != senha.get_secret_value():
        print("As senhas não conferem.")
        return 1

    with Session(obter_engine()) as sessao:
        try:
            usuario = criar_usuario(
                sessao,
                nome_completo=nome_completo,
                email=email,
                tipo=TipoUsuario.PROFESSOR,
                senha_hash=hash_senha(senha.get_secret_value()),
            )
        except EmailJaCadastrado:
            print("Já existe um usuário com esse e-mail.")
            return 1
        sessao.commit()
        print(f"Professor(a) criado(a) com id {usuario.id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""TEMPORÁRIO, para a apresentação. Conclui o primeiro acesso de alunos sem passar pelo
código do e-mail, como se o aluno tivesse usado o app. Se o e-mail informado não
existir, cria o aluno direto no banco (sem enviar e-mail).

Uso: poetry run python -m src.scripts.simular_primeiro_acesso
Apague este arquivo depois da apresentação.
"""

import random
import sys
from datetime import datetime
from getpass import getpass

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import obter_engine
from src.models.usuario import TipoUsuario, Usuario
from src.schemas.aluno import (
    MAIORIDADE,
    PrimeiroAcessoAlunoEntrada,
    calcular_idade,
    hoje,
)
from src.schemas.tipos import Email, NomeCompleto, NovaSenha
from src.scripts.criar_professor import _escolher_banco
from src.services.usuario_service import (
    CpfJaCadastrado,
    EmailJaCadastrado,
    PrimeiroAcessoJaConcluido,
    concluir_primeiro_acesso_aluno,
    criar_usuario,
)


def _cpf_valido() -> str:
    """CPF com dígitos verificadores corretos, só para dados de teste."""
    while True:
        digitos = [random.randint(0, 9) for _ in range(9)]
        if len(set(digitos)) > 1:
            break
    for _ in range(2):
        pesos = range(len(digitos) + 1, 1, -1)
        resto = (sum(d * p for d, p in zip(digitos, pesos)) * 10) % 11
        digitos.append(0 if resto == 10 else resto)
    return "".join(str(d) for d in digitos)


def _telefone() -> str:
    return "119" + "".join(str(random.randint(0, 9)) for _ in range(8))


def _concluir(sessao: Session, usuario: Usuario, senha: str) -> None:
    try:
        nascimento = datetime.strptime(  # noqa: DTZ007
            input("Data de nascimento (DD/MM/AAAA): ").strip(), "%d/%m/%Y"
        ).date()
    except ValueError:
        print("Data inválida.")
        return

    if calcular_idade(nascimento, hoje()) < MAIORIDADE:
        responsavel = input("Nome completo do responsável (menor de idade): ").strip()
        de_quem = " do responsável"
    else:
        responsavel = None
        de_quem = ""

    cpf = input(f"CPF{de_quem} (Enter gera um válido): ").strip() or _cpf_valido()
    telefone = input(f"Telefone{de_quem} (Enter gera um): ").strip() or _telefone()

    try:
        dados = PrimeiroAcessoAlunoEntrada(
            data_nascimento=nascimento,
            cpf=cpf,
            telefone=telefone,
            responsavel_nome=responsavel,
            nova_senha=senha,
        )
    except ValidationError as erro:
        print("Dado inválido: " + "; ".join(item["msg"] for item in erro.errors()))
        return

    try:
        concluir_primeiro_acesso_aluno(
            sessao,
            usuario,
            data_nascimento=dados.data_nascimento,
            possui_responsavel=dados.possui_responsavel,
            cpf=dados.cpf,
            telefone=dados.telefone,
            responsavel_nome=dados.responsavel_nome,
            nova_senha=dados.nova_senha.get_secret_value(),
        )
    except PrimeiroAcessoJaConcluido:
        print("Esse aluno já concluiu o primeiro acesso.")
        return
    except CpfJaCadastrado:
        print("Já existe um aluno com esse CPF.")
        return
    print(f"Primeiro acesso concluído: {usuario.nome_completo} ({usuario.email}).")


def main() -> int:
    if not _escolher_banco():
        return 1
    try:
        senha = (
            TypeAdapter(NovaSenha)
            .validate_python(getpass("Senha dos alunos de teste: "))
            .get_secret_value()
        )
    except ValidationError as erro:
        print("Senha inválida: " + "; ".join(item["msg"] for item in erro.errors()))
        return 1

    with Session(obter_engine()) as sessao:
        while True:
            pendentes = sessao.scalars(
                select(Usuario.email)
                .where(
                    Usuario.tipo == TipoUsuario.ALUNO,
                    Usuario.senha.is_(None),
                    Usuario.deletado_em.is_(None),
                )
                .order_by(Usuario.id)
            ).all()
            print("\nAlunos com primeiro acesso pendente:")
            print("\n".join(f"  - {email}" for email in pendentes) or "  (nenhum)")

            entrada = input("\nE-mail do aluno (Enter para sair): ").strip()
            if not entrada:
                return 0
            try:
                email = TypeAdapter(Email).validate_python(entrada)
            except ValidationError:
                print("E-mail inválido.")
                continue

            usuario = sessao.scalar(select(Usuario).where(Usuario.email == email))
            if usuario is None:
                nome = input("Aluno não existe. Nome completo para criá-lo: ").strip()
                if not nome:
                    continue
                try:
                    nome = TypeAdapter(NomeCompleto).validate_python(nome)
                    usuario = criar_usuario(
                        sessao, nome_completo=nome, email=email, tipo=TipoUsuario.ALUNO
                    )
                    sessao.commit()
                except ValidationError as erro:
                    print(
                        "Nome inválido: " + "; ".join(i["msg"] for i in erro.errors())
                    )
                    continue
                except EmailJaCadastrado:
                    print("Esse e-mail já está em uso.")
                    continue
            elif usuario.tipo != TipoUsuario.ALUNO or usuario.deletado_em is not None:
                print("Esse e-mail não é de um aluno ativo.")
                continue

            _concluir(sessao, usuario, senha)


if __name__ == "__main__":
    sys.exit(main())



## teste
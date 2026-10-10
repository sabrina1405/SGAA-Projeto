from datetime import date

import pytest
from pydantic import ValidationError

from src.schemas.aluno import PrimeiroAcessoAlunoEntrada, calcular_idade
from src.schemas.auth import LoginEntrada, RedefinirSenhaEntrada
from src.schemas.usuario import AlunoCriar
from tests.conftest import nascido_ha


def _entrada_aluno(**campos):
    dados = {
        "data_nascimento": nascido_ha(30),
        "cpf": "52998224725",
        "telefone": "11912345678",
        "nova_senha": "Senha-Valida-1",
    }
    return PrimeiroAcessoAlunoEntrada(**{**dados, **campos})


def test_email_e_normalizado():
    dados = AlunoCriar(nome_completo="Maria Silva", email="  Maria.Silva@Exemplo.COM ")
    assert dados.email == "maria.silva@exemplo.com"


@pytest.mark.parametrize(
    "email", ["sem-arroba", "a@", "@b.com", "a" * 80 + "@exemplo.com"]
)
def test_email_invalido(email):
    with pytest.raises(ValidationError):
        AlunoCriar(nome_completo="Maria Silva", email=email)


def test_nome_e_higienizado():
    dados = AlunoCriar(nome_completo="  Maria \t  da   Silva\n", email="m@exemplo.com")
    assert dados.nome_completo == "Maria da Silva"


def test_nome_e_normalizado_para_nfc():
    decomposto = "José Silva"
    dados = AlunoCriar(nome_completo=decomposto, email="j@exemplo.com")
    assert dados.nome_completo == "José Silva"


@pytest.mark.parametrize(
    "nome", ["", "ab", "   a   ", "x" * 101, "Maria\x00Silva", "Ma\u200bria"]
)
def test_nome_invalido(nome):
    with pytest.raises(ValidationError):
        AlunoCriar(nome_completo=nome, email="m@exemplo.com")


def test_campo_desconhecido_e_rejeitado():
    with pytest.raises(ValidationError):
        AlunoCriar(nome_completo="Maria Silva", email="m@exemplo.com", tipo="professor")


@pytest.mark.parametrize(
    "senha",
    [
        "Ab-_1",  # curta
        "Aa-_" + "x" * 97,  # longa
        "sem-maiuscula-1",
        "SEM-MINUSCULA-1",
        "SoUmEspecial-1",
        "Sem Especiais 12",  # espaço não conta como especial
    ],
)
def test_nova_senha_invalida(senha):
    with pytest.raises(ValidationError):
        RedefinirSenhaEntrada(email="m@exemplo.com", codigo="123456", nova_senha=senha)


@pytest.mark.parametrize("senha", ["Ab-_cd", "Aa-_" + "x" * 96, "Çé@#!?", "Senha!!"])
def test_nova_senha_valida(senha):
    dados = RedefinirSenhaEntrada(
        email="m@exemplo.com", codigo="123456", nova_senha=senha
    )
    assert dados.nova_senha.get_secret_value() == senha


def test_nova_senha_nao_sofre_strip():
    dados = RedefinirSenhaEntrada(
        email="m@exemplo.com", codigo="123456", nova_senha="  Com-Espacos!  "
    )
    assert dados.nova_senha.get_secret_value() == "  Com-Espacos!  "


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("529.982.247-25", "52998224725"), (" 52998224725 ", "52998224725")],
)
def test_cpf_e_guardado_so_com_digitos(entrada, esperado):
    assert _entrada_aluno(cpf=entrada).cpf == esperado


@pytest.mark.parametrize(
    "cpf", ["52998224724", "11111111111", "5299822472", "529982247255", "5299822472a"]
)
def test_cpf_invalido(cpf):
    with pytest.raises(ValidationError):
        _entrada_aluno(cpf=cpf)


def test_telefone_e_guardado_so_com_digitos():
    assert _entrada_aluno(telefone="(11) 91234-5678").telefone == "11912345678"
    assert _entrada_aluno(telefone="1132345678").telefone == "1132345678"


@pytest.mark.parametrize("telefone", ["912345678", "119123456789", "01912345678", "x"])
def test_telefone_invalido(telefone):
    with pytest.raises(ValidationError):
        _entrada_aluno(telefone=telefone)


def test_idade_considera_se_ja_fez_aniversario():
    assert calcular_idade(date(2008, 10, 7), date(2026, 10, 7)) == 18
    assert calcular_idade(date(2008, 10, 8), date(2026, 10, 7)) == 17
    assert calcular_idade(date(2008, 2, 29), date(2026, 2, 28)) == 17


def test_menor_exige_nome_do_responsavel():
    nascimento = nascido_ha(17)
    with pytest.raises(ValidationError):
        _entrada_aluno(data_nascimento=nascimento)
    dados = _entrada_aluno(data_nascimento=nascimento, responsavel_nome="Ana  Souza")
    assert dados.possui_responsavel
    assert dados.responsavel_nome == "Ana Souza"


def test_maior_nao_pode_informar_responsavel():
    nascimento = nascido_ha(18)
    assert not _entrada_aluno(data_nascimento=nascimento).possui_responsavel
    with pytest.raises(ValidationError):
        _entrada_aluno(data_nascimento=nascimento, responsavel_nome="Ana Souza")


@pytest.mark.parametrize("anos", [-1, 0, 121])
def test_data_de_nascimento_invalida(anos):
    with pytest.raises(ValidationError):
        _entrada_aluno(data_nascimento=nascido_ha(anos))


def test_nova_senha_igual_ao_email_e_rejeitada():
    with pytest.raises(ValidationError):
        RedefinirSenhaEntrada(
            email="maria@exemplo.com", codigo="123456", nova_senha="Maria@exemplo.com"
        )


@pytest.mark.parametrize("codigo", ["12345", "1234567", "12a456", "１２３４５６", ""])
def test_codigo_invalido(codigo):
    with pytest.raises(ValidationError):
        RedefinirSenhaEntrada(
            email="m@exemplo.com", codigo=codigo, nova_senha="Senha-Valida-1"
        )


def test_senha_nao_aparece_no_repr():
    dados = LoginEntrada(email="m@exemplo.com", senha="segredo-123")
    assert "segredo-123" not in repr(dados)

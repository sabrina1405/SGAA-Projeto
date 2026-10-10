from src.models.usuario import TipoUsuario, Usuario
from tests.conftest import cabecalho, nascido_ha

NOVO_ALUNO = {"nome_completo": "  João   da Silva ", "email": "Joao@Exemplo.com"}


def test_professor_cadastra_aluno_e_aluno_define_a_senha(
    client, professor, enviador, sessao
):
    resposta = client.post(
        "/usuarios/alunos", json=NOVO_ALUNO, headers=cabecalho(professor)
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome_completo"] == "João da Silva"
    assert corpo["email"] == "joao@exemplo.com"
    assert corpo["tipo"] == "aluno"
    assert "senha" not in corpo

    criado = sessao.get(Usuario, corpo["id"])
    assert criado.senha is None
    assert criado.tipo == TipoUsuario.ALUNO
    assert enviador.mensagens[-1]["para"] == "joao@exemplo.com"

    # Sem senha definida, o aluno ainda não consegue entrar.
    login = {"email": "joao@exemplo.com", "senha": "Senha-Do-Joao-1"}
    assert client.post("/auth/login", json=login).status_code == 401

    # O código do convite serve direto no passo de validação do primeiro acesso.
    resposta = client.post(
        "/auth/primeiro-acesso/validar-codigo",
        json={"email": "joao@exemplo.com", "codigo": enviador.ultimo_codigo()},
    )
    assert resposta.status_code == 200
    token = resposta.json()["token_primeiro_acesso"]

    resposta = client.post(
        "/auth/primeiro-acesso/aluno",
        json={
            "data_nascimento": nascido_ha(20).isoformat(),
            "cpf": "529.982.247-25",
            "telefone": "(11) 91234-5678",
            "nova_senha": "Senha-Do-Joao-1",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 200
    assert client.post("/auth/login", json=login).status_code == 200


def test_aluno_nao_pode_cadastrar_aluno(client, aluno):
    resposta = client.post(
        "/usuarios/alunos", json=NOVO_ALUNO, headers=cabecalho(aluno)
    )
    assert resposta.status_code == 403


def test_cadastro_exige_autenticacao(client):
    assert client.post("/usuarios/alunos", json=NOVO_ALUNO).status_code == 401


def test_email_duplicado(client, professor, aluno):
    resposta = client.post(
        "/usuarios/alunos",
        json={"nome_completo": "Outro Aluno", "email": aluno.email.upper()},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 409


def test_front_nao_escolhe_o_tipo(client, professor):
    resposta = client.post(
        "/usuarios/alunos",
        json={**NOVO_ALUNO, "tipo": "professor"},
        headers=cabecalho(professor),
    )
    assert resposta.status_code == 422


def test_falha_no_email_desfaz_o_cadastro(client, professor, enviador, sessao):
    enviador.falhar = True
    resposta = client.post(
        "/usuarios/alunos", json=NOVO_ALUNO, headers=cabecalho(professor)
    )
    assert resposta.status_code == 502
    assert sessao.query(Usuario).filter_by(email="joao@exemplo.com").first() is None

    enviador.falhar = False
    resposta = client.post(
        "/usuarios/alunos", json=NOVO_ALUNO, headers=cabecalho(professor)
    )
    assert resposta.status_code == 201

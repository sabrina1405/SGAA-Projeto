from src.models.aluno import Aluno
from src.models.usuario import TipoUsuario
from tests.conftest import cabecalho, nascido_ha

SENHA = "Senha-Nova-1!"
CPF = "52998224725"
OUTRO_CPF = "11144477735"
TELEFONE = "11912345678"


def _formulario(**campos):
    dados = {
        "data_nascimento": nascido_ha(25).isoformat(),
        "cpf": CPF,
        "telefone": TELEFONE,
        "nova_senha": SENHA,
    }
    return {**dados, **campos}


def _formulario_de_menor(**campos):
    return _formulario(
        data_nascimento=nascido_ha(15).isoformat(),
        responsavel_nome="Ana Souza",
        **campos,
    )


def _validar_codigo(client, enviador, email):
    """Pede o código e o troca pelo cabeçalho com o token de primeiro acesso."""
    assert (
        client.post("/auth/primeiro-acesso/codigo", json={"email": email}).status_code
        == 202
    )
    resposta = client.post(
        "/auth/primeiro-acesso/validar-codigo",
        json={"email": email, "codigo": enviador.ultimo_codigo()},
    )
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['token_primeiro_acesso']}"}


def _concluir(client, headers, **campos):
    return client.post(
        "/auth/primeiro-acesso/aluno", json=_formulario(**campos), headers=headers
    )


def test_primeiro_acesso_de_aluno_maior_de_idade(
    client, criar_usuario, enviador, sessao
):
    usuario = criar_usuario("novo@exemplo.com", senha=None)

    resposta = client.post(
        "/auth/primeiro-acesso/codigo", json={"email": "novo@exemplo.com"}
    )
    assert resposta.status_code == 202
    resposta = client.post(
        "/auth/primeiro-acesso/validar-codigo",
        json={"email": "novo@exemplo.com", "codigo": enviador.ultimo_codigo()},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["expires_in"] == 30 * 60
    assert corpo["usuario"]["tipo"] == "aluno"

    resposta = _concluir(
        client, {"Authorization": f"Bearer {corpo['token_primeiro_acesso']}"}
    )
    assert resposta.status_code == 200
    assert SENHA not in resposta.text

    # O formulário já devolve o token de acesso: não é preciso fazer login.
    acesso = {"Authorization": f"Bearer {resposta.json()['access_token']}"}
    assert client.get("/auth/me", headers=acesso).json()["id"] == usuario.id
    login = {"email": "novo@exemplo.com", "senha": SENHA}
    assert client.post("/auth/login", json=login).status_code == 200

    perfil = sessao.get(Aluno, usuario.id)
    assert perfil.data_nascimento == nascido_ha(25)
    assert not perfil.possui_responsavel
    assert (perfil.cpf, perfil.telefone) == (CPF, TELEFONE)
    assert perfil.responsavel_nome is None
    assert perfil.responsavel_cpf is None
    assert perfil.responsavel_telefone is None


def test_primeiro_acesso_de_menor_guarda_os_dados_do_responsavel(
    client, criar_usuario, enviador, sessao
):
    usuario = criar_usuario("menor@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "menor@exemplo.com")

    resposta = client.post(
        "/auth/primeiro-acesso/aluno", json=_formulario_de_menor(), headers=headers
    )
    assert resposta.status_code == 200

    perfil = sessao.get(Aluno, usuario.id)
    assert perfil.possui_responsavel
    assert perfil.responsavel_nome == "Ana Souza"
    assert (perfil.responsavel_cpf, perfil.responsavel_telefone) == (CPF, TELEFONE)
    assert perfil.cpf is None
    assert perfil.telefone is None


def test_irmaos_podem_ter_o_mesmo_responsavel(client, criar_usuario, enviador):
    for email in ("irmao1@exemplo.com", "irmao2@exemplo.com"):
        criar_usuario(email, senha=None)
        headers = _validar_codigo(client, enviador, email)
        resposta = client.post(
            "/auth/primeiro-acesso/aluno", json=_formulario_de_menor(), headers=headers
        )
        assert resposta.status_code == 200


def test_menor_sem_nome_do_responsavel_e_recusado(client, criar_usuario, enviador):
    criar_usuario("menor@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "menor@exemplo.com")
    resposta = _concluir(client, headers, data_nascimento=nascido_ha(15).isoformat())
    assert resposta.status_code == 422
    assert SENHA not in resposta.text


def test_maior_com_responsavel_e_recusado(client, criar_usuario, enviador):
    criar_usuario("maior@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "maior@exemplo.com")
    resposta = _concluir(client, headers, responsavel_nome="Ana Souza")
    assert resposta.status_code == 422


def test_cpf_de_aluno_nao_pode_repetir(client, criar_usuario, enviador):
    criar_usuario("primeiro@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "primeiro@exemplo.com")
    assert _concluir(client, headers).status_code == 200

    criar_usuario("segundo@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "segundo@exemplo.com")
    assert _concluir(client, headers).status_code == 409

    # O erro não consome o token: basta corrigir o formulário e reenviar.
    login = {"email": "segundo@exemplo.com", "senha": SENHA}
    assert client.post("/auth/login", json=login).status_code == 401
    assert _concluir(client, headers, cpf=OUTRO_CPF).status_code == 200
    assert client.post("/auth/login", json=login).status_code == 200


def test_token_de_primeiro_acesso_nao_serve_como_token_de_acesso(
    client, criar_usuario, enviador
):
    criar_usuario("novo@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "novo@exemplo.com")
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.post("/auth/renovar", headers=headers).status_code == 401


def test_token_de_acesso_nao_serve_no_primeiro_acesso(client, criar_usuario, aluno):
    sem_senha = criar_usuario("novo@exemplo.com", senha=None)
    for usuario in (aluno, sem_senha):
        assert _concluir(client, cabecalho(usuario)).status_code == 401
    sem_token = client.post("/auth/primeiro-acesso/aluno", json=_formulario())
    assert sem_token.status_code == 401


def test_primeiro_acesso_so_pode_ser_concluido_uma_vez(client, criar_usuario, enviador):
    criar_usuario("novo@exemplo.com", senha=None)
    headers = _validar_codigo(client, enviador, "novo@exemplo.com")
    assert _concluir(client, headers).status_code == 200
    assert _concluir(client, headers, cpf=OUTRO_CPF).status_code == 401


def test_codigo_de_primeiro_acesso_so_vale_uma_vez(client, criar_usuario, enviador):
    criar_usuario("novo@exemplo.com", senha=None)
    _validar_codigo(client, enviador, "novo@exemplo.com")
    resposta = client.post(
        "/auth/primeiro-acesso/validar-codigo",
        json={"email": "novo@exemplo.com", "codigo": enviador.ultimo_codigo()},
    )
    assert resposta.status_code == 400


def test_codigo_errado_no_primeiro_acesso(client, criar_usuario, enviador):
    criar_usuario("novo@exemplo.com", senha=None)
    client.post("/auth/primeiro-acesso/codigo", json={"email": "novo@exemplo.com"})
    correto = enviador.ultimo_codigo()
    errado = "000000" if correto != "000000" else "111111"
    resposta = client.post(
        "/auth/primeiro-acesso/validar-codigo",
        json={"email": "novo@exemplo.com", "codigo": errado},
    )
    assert resposta.status_code == 400


def test_primeiro_acesso_nao_atende_quem_ja_tem_senha(client, aluno, enviador):
    com_senha = client.post("/auth/primeiro-acesso/codigo", json={"email": aluno.email})
    inexistente = client.post(
        "/auth/primeiro-acesso/codigo", json={"email": "ninguem@exemplo.com"}
    )
    assert com_senha.status_code == inexistente.status_code == 202
    assert com_senha.json() == inexistente.json()
    assert enviador.mensagens == []

    # Um código de redefinição de senha não abre o primeiro acesso.
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    resposta = client.post(
        "/auth/primeiro-acesso/validar-codigo",
        json={"email": aluno.email, "codigo": enviador.ultimo_codigo()},
    )
    assert resposta.status_code == 400


def test_esqueci_senha_nao_atende_quem_nao_fez_o_primeiro_acesso(
    client, criar_usuario, enviador
):
    criar_usuario("novo@exemplo.com", senha=None)
    resposta = client.post("/auth/esqueci-senha", json={"email": "novo@exemplo.com"})
    assert resposta.status_code == 202
    assert enviador.mensagens == []

    # O código de primeiro acesso não define a senha sem o formulário do perfil.
    client.post("/auth/primeiro-acesso/codigo", json={"email": "novo@exemplo.com"})
    resposta = client.post(
        "/auth/redefinir-senha",
        json={
            "email": "novo@exemplo.com",
            "codigo": enviador.ultimo_codigo(),
            "nova_senha": SENHA,
        },
    )
    assert resposta.status_code == 400
    login = {"email": "novo@exemplo.com", "senha": SENHA}
    assert client.post("/auth/login", json=login).status_code == 401


def test_formulario_de_aluno_recusa_professor(client, criar_usuario, enviador):
    criar_usuario("prof@exemplo.com", TipoUsuario.PROFESSOR, senha=None)
    headers = _validar_codigo(client, enviador, "prof@exemplo.com")
    assert _concluir(client, headers).status_code == 403

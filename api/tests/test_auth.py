from datetime import timedelta

import jwt

from src.core.config import obter_config
from src.core.security import agora, criar_token
from src.models.codigo_verificacao import CodigoVerificacao
from src.models.usuario import TipoUsuario
from src.services import auth_service
from tests.conftest import SENHA_PADRAO, cabecalho


def _login(client, email, senha=SENHA_PADRAO):
    return client.post("/auth/login", json={"email": email, "senha": senha})


# --- login ---


def test_login_com_sucesso(client, aluno):
    resposta = _login(client, "  ALUNO@exemplo.com ")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["expires_in"] == 30 * 24 * 3600
    assert corpo["usuario"] == {
        "id": aluno.id,
        "nome_completo": aluno.nome_completo,
        "email": "aluno@exemplo.com",
        "tipo": "aluno",
    }
    me = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {corpo['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["id"] == aluno.id


def test_login_falhas_tem_a_mesma_resposta(client, aluno, criar_usuario, sessao):
    criar_usuario("sem-senha@exemplo.com", senha=None)
    removido = criar_usuario("removido@exemplo.com")
    removido.deletado_em = agora()
    sessao.commit()

    respostas = [
        _login(client, "aluno@exemplo.com", "senha-errada"),
        _login(client, "nao-existe@exemplo.com"),
        _login(client, "sem-senha@exemplo.com"),
        _login(client, "removido@exemplo.com"),
    ]
    assert {r.status_code for r in respostas} == {401}
    assert len({r.text for r in respostas}) == 1


def test_login_bloqueia_apos_muitas_falhas(client, aluno, sessao):
    for _ in range(auth_service.MAX_TENTATIVAS_LOGIN):
        assert _login(client, aluno.email, "senha-errada").status_code == 401
    assert aluno.bloqueado_ate is not None

    # Bloqueado: nem a senha correta entra, e a resposta é a mesma.
    assert _login(client, aluno.email).status_code == 401

    aluno.bloqueado_ate = agora() - timedelta(seconds=1)
    sessao.commit()
    assert _login(client, aluno.email).status_code == 200
    assert aluno.bloqueado_ate is None


def test_login_com_sucesso_zera_tentativas(client, aluno):
    _login(client, aluno.email, "senha-errada")
    assert aluno.tentativas_login == 1
    assert _login(client, aluno.email).status_code == 200
    assert aluno.tentativas_login == 0


def test_erro_de_validacao_nao_ecoa_a_senha(client):
    resposta = client.post(
        "/auth/login",
        json={"email": "invalido", "senha": "minha-senha-secreta", "x": 1},
    )
    assert resposta.status_code == 422
    assert "minha-senha-secreta" not in resposta.text
    assert {tuple(erro["loc"]) for erro in resposta.json()["detail"]} == {
        ("body", "email"),
        ("body", "x"),
    }


# --- token e autorização ---


def test_rota_protegida_sem_token(client):
    resposta = client.get("/auth/me")
    assert resposta.status_code == 401
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_rota_protegida_com_token_malformado(client):
    resposta = client.get("/auth/me", headers={"Authorization": "Bearer nao-e-um-jwt"})
    assert resposta.status_code == 401


def test_token_expirado(client, aluno):
    chave = obter_config().secret_key.get_secret_value()
    expirado = jwt.encode(
        {"sub": str(aluno.id), "tv": 0, "exp": agora() - timedelta(minutes=1)},
        chave,
        algorithm="HS256",
    )
    resposta = client.get("/auth/me", headers={"Authorization": f"Bearer {expirado}"})
    assert resposta.status_code == 401


def test_token_assinado_com_outra_chave(client, aluno):
    forjado = jwt.encode(
        {"sub": str(aluno.id), "tv": 0, "exp": agora() + timedelta(hours=1)},
        "outra-chave-qualquer-com-mais-de-32-caracteres",
        algorithm="HS256",
    )
    resposta = client.get("/auth/me", headers={"Authorization": f"Bearer {forjado}"})
    assert resposta.status_code == 401


def test_token_sem_assinatura_e_recusado(client, aluno):
    sem_assinatura = jwt.encode(
        {"sub": str(aluno.id), "tv": 0, "exp": agora() + timedelta(hours=1)},
        None,
        algorithm="none",
    )
    resposta = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {sem_assinatura}"}
    )
    assert resposta.status_code == 401


def test_token_de_usuario_removido(client, aluno, sessao):
    headers = cabecalho(aluno)
    aluno.deletado_em = agora()
    sessao.commit()
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_sair_de_todos_invalida_tokens_antigos(client, aluno):
    headers = cabecalho(aluno)
    assert client.post("/auth/sair-de-todos", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.get("/auth/me", headers=cabecalho(aluno)).status_code == 200


def test_renovar_devolve_token_valido(client, aluno):
    resposta = client.post("/auth/renovar", headers=cabecalho(aluno))
    assert resposta.status_code == 200
    novo = resposta.json()["access_token"]
    assert (
        client.get("/auth/me", headers={"Authorization": f"Bearer {novo}"}).status_code
        == 200
    )


def test_renovar_exige_token(client):
    assert client.post("/auth/renovar").status_code == 401


# --- recuperação de senha ---


def _codigo_ativo(sessao, usuario):
    return (
        sessao.query(CodigoVerificacao)
        .filter_by(usuario_id=usuario.id, usado_em=None)
        .one()
    )


def test_recuperacao_de_senha_fluxo_completo(client, aluno, enviador):
    token_antigo = cabecalho(aluno)

    resposta = client.post("/auth/esqueci-senha", json={"email": aluno.email})
    assert resposta.status_code == 202
    assert enviador.mensagens[-1]["para"] == aluno.email

    resposta = client.post(
        "/auth/redefinir-senha",
        json={
            "email": aluno.email,
            "codigo": enviador.ultimo_codigo(),
            "nova_senha": "Nova-Senha-456",
        },
    )
    assert resposta.status_code == 204

    assert _login(client, aluno.email).status_code == 401
    assert _login(client, aluno.email, "Nova-Senha-456").status_code == 200
    assert client.get("/auth/me", headers=token_antigo).status_code == 401


def test_esqueci_senha_nao_revela_se_o_email_existe(client, aluno, enviador):
    existente = client.post("/auth/esqueci-senha", json={"email": aluno.email})
    inexistente = client.post(
        "/auth/esqueci-senha", json={"email": "ninguem@exemplo.com"}
    )
    assert existente.status_code == inexistente.status_code == 202
    assert existente.json() == inexistente.json()
    assert len(enviador.mensagens) == 1


def test_esqueci_senha_responde_202_mesmo_se_o_envio_falhar(client, aluno, enviador):
    enviador.falhar = True
    assert (
        client.post("/auth/esqueci-senha", json={"email": aluno.email}).status_code
        == 202
    )


def test_codigo_nao_e_guardado_em_texto_puro(client, aluno, enviador, sessao):
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    registro = _codigo_ativo(sessao, aluno)
    assert registro.codigo_hash != enviador.ultimo_codigo()
    assert len(registro.codigo_hash) == 64


def test_codigo_errado_e_recusado_e_limite_de_tentativas(client, aluno, enviador):
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    correto = enviador.ultimo_codigo()
    errado = "000000" if correto != "000000" else "111111"

    corpo = {"email": aluno.email, "nova_senha": "Nova-Senha-456"}
    for _ in range(auth_service.MAX_TENTATIVAS_CODIGO):
        resposta = client.post(
            "/auth/redefinir-senha", json={**corpo, "codigo": errado}
        )
        assert resposta.status_code == 400

    # Esgotadas as tentativas, nem o código correto funciona.
    resposta = client.post("/auth/redefinir-senha", json={**corpo, "codigo": correto})
    assert resposta.status_code == 400
    assert _login(client, aluno.email).status_code == 200


def test_codigo_expirado(client, aluno, enviador, sessao):
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    _codigo_ativo(sessao, aluno).expira_em = agora() - timedelta(seconds=1)
    sessao.commit()

    resposta = client.post(
        "/auth/redefinir-senha",
        json={
            "email": aluno.email,
            "codigo": enviador.ultimo_codigo(),
            "nova_senha": "Nova-Senha-456",
        },
    )
    assert resposta.status_code == 400


def test_codigo_nao_pode_ser_reutilizado(client, aluno, enviador):
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    corpo = {
        "email": aluno.email,
        "codigo": enviador.ultimo_codigo(),
        "nova_senha": "Nova-Senha-456",
    }
    assert client.post("/auth/redefinir-senha", json=corpo).status_code == 204
    corpo["nova_senha"] = "Outra-Senha-789"
    assert client.post("/auth/redefinir-senha", json=corpo).status_code == 400


def test_codigo_de_outro_usuario_nao_serve(client, aluno, professor, enviador):
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    resposta = client.post(
        "/auth/redefinir-senha",
        json={
            "email": professor.email,
            "codigo": enviador.ultimo_codigo(),
            "nova_senha": "Nova-Senha-456",
        },
    )
    assert resposta.status_code == 400


def test_intervalo_minimo_entre_codigos(client, aluno, enviador, sessao):
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    assert (
        client.post("/auth/esqueci-senha", json={"email": aluno.email}).status_code
        == 202
    )
    assert len(enviador.mensagens) == 1

    primeiro = enviador.ultimo_codigo()
    _codigo_ativo(sessao, aluno).criado_em = agora() - timedelta(minutes=2)
    sessao.commit()
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    assert len(enviador.mensagens) == 2

    # O código anterior deixa de valer quando um novo é emitido.
    if enviador.ultimo_codigo() != primeiro:
        resposta = client.post(
            "/auth/redefinir-senha",
            json={
                "email": aluno.email,
                "codigo": primeiro,
                "nova_senha": "Nova-Senha-456",
            },
        )
        assert resposta.status_code == 400


def test_limite_de_codigos_por_hora(client, aluno, enviador, sessao):
    for _ in range(auth_service.MAX_CODIGOS_POR_JANELA + 2):
        client.post("/auth/esqueci-senha", json={"email": aluno.email})
        for registro in sessao.query(CodigoVerificacao).filter_by(usuario_id=aluno.id):
            if agora() - registro.criado_em < timedelta(minutes=2):
                registro.criado_em = agora() - timedelta(minutes=2)
        sessao.commit()
    assert len(enviador.mensagens) == auth_service.MAX_CODIGOS_POR_JANELA


def test_redefinir_senha_desbloqueia_o_login(client, aluno, enviador, sessao):
    aluno.bloqueado_ate = agora() + timedelta(minutes=10)
    sessao.commit()
    client.post("/auth/esqueci-senha", json={"email": aluno.email})
    client.post(
        "/auth/redefinir-senha",
        json={
            "email": aluno.email,
            "codigo": enviador.ultimo_codigo(),
            "nova_senha": "Nova-Senha-456",
        },
    )
    assert _login(client, aluno.email, "Nova-Senha-456").status_code == 200


def test_token_carrega_a_versao_do_usuario(aluno):
    claims = jwt.decode(
        criar_token(aluno.id, aluno.versao_token),
        obter_config().secret_key.get_secret_value(),
        algorithms=["HS256"],
    )
    assert claims["sub"] == str(aluno.id)
    assert claims["tv"] == aluno.versao_token
    assert aluno.tipo == TipoUsuario.ALUNO

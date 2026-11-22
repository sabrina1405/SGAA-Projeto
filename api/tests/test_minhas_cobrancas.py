from datetime import timedelta

from src.models.professor import Professor
from src.schemas.aluno import hoje
from tests.conftest import cabecalho
from tests.test_financeiro import _avulsa

ROTA = "/v1/minhas-cobrancas"


def test_rotas_sao_do_aluno(client, professor):
    for rota in (ROTA, f"{ROTA}/1"):
        assert client.get(rota).status_code == 401
        assert client.get(rota, headers=cabecalho(professor)).status_code == 403


def test_aluno_ve_as_proprias_cobrancas_com_a_chave_pix(
    client, sessao, professor, outro_professor, aluno_maior, criar_aluno_com_perfil
):
    sessao.get(Professor, professor.id).chave_pix = "professora@exemplo.com"
    sessao.commit()
    outro = criar_aluno_com_perfil("outro@exemplo.com", anos=15, nome_completo="Bia")
    vencida = _avulsa(
        client, professor, aluno_maior, vencimento=hoje() - timedelta(days=2)
    )
    futura = _avulsa(client, outro_professor, aluno_maior)
    de_outro = _avulsa(client, professor, outro)

    resposta = client.get(ROTA, headers=cabecalho(aluno_maior)).json()["dados"]
    assert [item["id"] for item in resposta["itens"]] == [futura["id"], vencida["id"]]
    item = resposta["itens"][1]
    assert item["situacao"] == "vencida"
    assert item["chave_pix"] == "professora@exemplo.com"
    assert item["professor_nome"] == professor.nome_completo
    assert resposta["itens"][0]["chave_pix"] is None

    filtrado = client.get(
        ROTA, params={"situacao": "vencida"}, headers=cabecalho(aluno_maior)
    ).json()["dados"]
    assert [item["id"] for item in filtrado["itens"]] == [vencida["id"]]

    detalhe = client.get(f"{ROTA}/{vencida['id']}", headers=cabecalho(aluno_maior))
    assert detalhe.json()["dados"]["valor_centavos"] == 5000
    assert (
        client.get(
            f"{ROTA}/{de_outro['id']}", headers=cabecalho(aluno_maior)
        ).status_code
        == 404
    )

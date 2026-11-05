# Auditoria de dependências

O [`pip-audit`](https://pypi.org/project/pip-audit/), mantido pela PyPA, consulta as vulnerabilidades conhecidas (CVEs) das dependências do projeto. Use antes de adicionar uma dependência nova e sempre que o `requirements.txt` mudar.

Os comandos são executados dentro de `api/` e precisam de acesso à internet.

## Instalar

Fora do projeto, para não entrar no `pyproject.toml` nem no deploy:

```bash
pipx install pip-audit
pip-audit --version
```

Sem o `pipx`, dá para instalar no `.venv` com `pip install pip-audit`, mas ele é removido se alguém rodar `poetry sync`.

## Auditar o que vai para a Vercel

```bash
pip-audit -r requirements.txt --no-deps --disable-pip
```

O `requirements.txt` é gerado pelo `poetry export` com todas as versões fixadas. Com essas duas opções o `pip-audit` só lê o arquivo, sem baixar nem instalar nada.

## Auditar o ambiente inteiro

Inclui as dependências de desenvolvimento (`pytest`, `ruff`...), que não aparecem no `requirements.txt`:

```bash
. .venv/bin/activate
pip-audit --local
```

## Auditar um pacote antes de instalar

```bash
echo "nome-do-pacote==1.2.3" > /tmp/candidato.txt
pip-audit -r /tmp/candidato.txt
```

O `pip-audit` resolve as dependências transitivas em um ambiente temporário e audita todas. Para isso ele baixa os pacotes, então confira o nome antes de rodar.

## Ler o resultado

- `No known vulnerabilities found`: nada a fazer.
- Quando há achados, sai uma tabela com pacote, versão, identificador da vulnerabilidade e a versão que corrige. Acrescente `--desc` para ver a descrição.
- O comando termina com código diferente de zero quando encontra algo.

A base padrão é a do PyPI. Para cruzar com a do OSV, repita o comando com `-s osv`.

## Limites

O `pip-audit` só encontra vulnerabilidades já catalogadas. Um pacote malicioso com nome parecido com o de um pacote legítimo (typosquatting) passa sem achados, então a conferência do nome exato no [PyPI](https://pypi.org) continua manual.

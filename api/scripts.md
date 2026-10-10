## Comandos úteis

Rodar o servidor: `poetry run uvicorn index:app --reload`

Rodar o servidor para testar pelo celular: `poetry run uvicorn index:app --host 0.0.0.0 --port 8000 --reload`

Gera o arquivo **requirements.txt** a partir do **poetry.lock**: `poetry export -f requirements.txt --output requirements.txt --without-hashes --only main`

**OBS**: caso o comando apresente erro, pode ser necessário instalar o plugin de export com `poetry self add poetry-plugin-export`

## Banco de dados e usuários

Aplicar as migrações: `poetry run alembic upgrade head`

Criar uma migração a partir dos modelos (use o próximo número da sequência em `alembic/versions/`): `poetry run alembic revision --autogenerate --rev-id 0003 -m "descricao"`

Desfazer a última migração: `poetry run alembic downgrade -1`

Aplicar as migrações em produção ou homologação (pede a URL do Session pooler do Supabase, porta 5432, e confirmação): `./aplicar_migracoes.sh`

Guia completo (criar, aplicar, trocar de branch, conflitos): [Migrações com Alembic](docs/banco_de_dados/migracoes_alembic.md)

Criar a conta da professora (pergunta se é no banco local ou em homologação/produção, e depois pede nome, e-mail e senha): `poetry run python -m src.scripts.criar_professor`

## Testes

**OBS**: os testes usam o banco da `DATABASE_URL`, aplicam as migrações nele e desfazem os dados ao fim de cada teste.

Rodar todos os testes `poetry run pytest`

Rodar com output detalhado `poetry run pytest -v`

### Lint e estilo

Verificar erros de lint `poetry run ruff check .`

Corrigir erros automáticos `poetry run ruff check --fix .`

Verificar formatação `poetry run ruff format --check .`

Aplicar formatação `poetry run ruff format .`

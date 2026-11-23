## Comandos úteis

Rodar o servidor: `poetry run uvicorn index:app --reload`

Rodar o servidor para testar pelo celular: `poetry run uvicorn index:app --host 0.0.0.0 --port 8000 --reload`

Gera o arquivo **requirements.txt** a partir do **poetry.lock**: `poetry export -f requirements.txt --output requirements.txt --without-hashes --only main`

**OBS**: caso o comando apresente erro, pode ser necessário instalar o plugin de export com `poetry self add poetry-plugin-export`

## Testes

Rodar todos os testes `poetry run pytest`

Rodar com output detalhado `poetry run pytest -v`

### Lint e estilo

Verificar erros de lint `poetry run ruff check .`

Corrigir erros automáticos `poetry run ruff check --fix .`

Verificar formatação `poetry run ruff format --check .`

Aplicar formatação `poetry run ruff format .`

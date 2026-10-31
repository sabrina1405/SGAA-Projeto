# API - SGAA

## Convenções

- Nomes de variáveis, funções e campos de tabelas do banco em português.
- Tabelas têm campos de auditoria: `criado_em`, `atualizado_em`, `deletado_em` (soft delete).

## Regras de trabalho

Comandos executados dentro de `api/`.

1. Antes de executar uma tarefa, rodar os linters e os testes automatizados, e rodar de novo ao concluir:
   - `poetry run ruff check .`
   - `poetry run ruff format --check .`
   - `poetry run pytest`
2. Executar as migrations (`poetry run alembic upgrade head`) antes dos testes e sempre que criar ou alterar uma migração. Ao criar uma, validar também o caminho de volta (`poetry run alembic downgrade -1` e `upgrade head` de novo).
3. Quando for pedido para organizar os commits, não executar `git commit`. Apenas colocar em staging os arquivos ou trechos de arquivos de cada grupo e sugerir no terminal a mensagem do commit (só o título, ou título com corpo). O commit é feito manualmente, depois de uma breve revisão do que foi separado.
4. O gerenciador de pacotes do projeto é o `poetry`. Antes de instalar qualquer dependência nova, parar e informar o nome exato do pacote, a versão e o motivo, e aguardar a confirmação. A conferência do nome e de CVEs para aquela versão é feita manualmente. Vale também para extras, plugins e dependências de desenvolvimento; nada de `poetry add` de pacote novo sem esse aval. O `pip-audit` serve só para verificar CVEs das versões ([Auditoria de Dependências](docs/auditoria_dependencias.md)), não para instalar pacotes.
5. Ao concluir um recurso novo ou alterar endpoints, atualizar o [guia do Postman](docs/postman.md). Cada endpoint com parâmetros na URL (caminho ou query) ou com corpo ganha:
   - o corpo da requisição em JSON (ou a URL com os parâmetros) do caminho feliz;
   - os principais caminhos de erro;
   - o status esperado de cada exemplo.

   Não incluir os corpos das respostas. Os endpoints sem parâmetros e sem corpo são apenas citados. O status de cada exemplo deve ser conferido com uma chamada real à API, por exemplo via `TestClient` contra o banco de testes.

Se o `poetry` não estiver disponível no ambiente (por exemplo, dentro do ai-jail), criar um venv em `api/.venv` (já ignorado pelo git), instalar o `poetry` nele e usar os comandos normalmente:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install poetry
poetry install
```

Se o `.venv` já existir, basta ativá-lo.

Os testes e as migrations precisam de um PostgreSQL acessível pela `DATABASE_URL`. Se não houver um disponível, subir um local com Docker:

```bash
docker run -d --name sgaa-test -p 5432:5432 \
  -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=sgaa_test \
  postgres:15
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/sgaa_test
```

Se não for possível rodar os testes ou as migrations, dizer isso explicitamente no resumo da tarefa em vez de apresentá-la como verificada.

## Contexto

- A API serve uma versão web e uma versão mobile (Android).
- A versão web e a API são deployadas na Vercel (serverless).

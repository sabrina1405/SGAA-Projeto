# Configuração da Máquina e Ambiente de Desenvolvimento

Este guia descreve os pré-requisitos e o passo a passo necessário para preparar o ambiente local antes de executar a API.

---

## 1. Pré-requisitos

Certifique-se de ter instalado em sua máquina:

- **Python**: Versão 3.12 ou 3.13 (exigido `>= 3.12`).
- **Poetry**: Gerenciador de dependências e ambientes virtuais (versão utilizada: **2.5.1**).
- **PostgreSQL**: Banco de dados relacional (versão 15 ou superior recomendada).
- **Git**: Controle de versão.

---

## 2. Instalação e Configuração do Poetry

Se você ainda não possui o Poetry instalado:

```bash
# Instalação via script oficial (Linux/macOS)
curl -sSL https://install.python-poetry.org | python3 -

# Ou via pipx
pipx install poetry==2.5.1
```

Caso já tenha o Poetry instalado e precise atualizar para a versão 2.5.1:

```bash
poetry self update 2.5.1
```

Verifique se a instalação foi bem-sucedida:

```bash
poetry --version
# Deve exibir: Poetry (version 2.5.1)
```

---

## 3. Instalação das Dependências do Projeto

Navegue até o diretório `api/` e instale todas as dependências (produção e desenvolvimento):

```bash
cd api
poetry install
```

> **Nota:** Este comando cria um ambiente virtual isolado para o projeto e instala pacotes principais (FastAPI, SQLAlchemy, Alembic, Psycopg3) e de desenvolvimento (Ruff, Pytest, HTTPX).

---

## 4. Configuração de Variáveis de Ambiente (`.env`)

Crie o arquivo `.env` na raiz do diretório `api/` a partir do template `.env.example`:

```bash
# Linux / macOS / Git Bash
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Windows (Prompt de Comando / CMD)
copy .env.example .env
```

Abra o arquivo `.env` gerado e configure as variáveis de acordo com o seu ambiente local:

```ini
# Configuração do Banco de Dados PostgreSQL
# Formato: postgresql+psycopg://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/sgaa_dev

# Configurações da Aplicação
# Mínimo de 32 caracteres. Gere com:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=troque_por_uma_chave_aleatoria_com_32_ou_mais_caracteres

# Origens permitidas para o front web (separadas por vírgula)
CORS_ORIGINS=http://localhost:8081

# "console" apenas loga os e-mails; "smtp" envia de verdade (ver .env.example)
EMAIL_BACKEND=console
```

> **Nota:** A API não inicia se `DATABASE_URL` ou `SECRET_KEY` estiverem ausentes ou se a `SECRET_KEY` tiver menos de 32 caracteres.

---

## 5. Configuração do Banco de Dados e Migrações

Com o PostgreSQL rodando localmente e o banco de dados criado:

> **Recomendação:** Para rodar o PostgreSQL na sua máquina é recomendado utilizar um **container Docker**, a **Supabase CLI** ou a própria plataforma web da Supabase.

1. Aplique as migrações existentes do Alembic para estruturar o banco:
   ```bash
   poetry run alembic upgrade head
   ```

2. Crie a conta da professora (não existe cadastro público; os alunos são cadastrados por ela):
   ```bash
   poetry run python -m src.scripts.criar_professor
   ```

---

## 6. Verificação do Ambiente

Para garantir que o ambiente está configurado corretamente, rode os comandos de validação:

1. **Verificar os testes automatizados:**
   ```bash
   poetry run pytest
   ```

2. **Verificar a formatação e lint do código:**
   ```bash
   poetry run ruff check .
   poetry run ruff format --check .
   ```

---

## Próximos Passos

Após concluir a configuração da máquina, consulte o documento [Iniciar Servidor Local](iniciar_servidor_local.md) para rodar a aplicação em modo de desenvolvimento.

# Changelog da API

Mudanças relevantes da API do SGAA, da versão mais nova para a mais antiga.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## Como manter

- Cada mudança entra em **Não lançado**, no mesmo PR que a implementa, em uma das seções: `Adicionado`, `Alterado`, `Corrigido`, `Removido` ou `Segurança`.
- Ao publicar uma versão (ir para produção):
  1. renomear **Não lançado** para `[X.Y.Z] - AAAA-MM-DD`
  2. abrir um **Não lançado** novo e vazio
  3. e atualizar a `version` do `pyproject.toml`.
- Cada versão registra a revisão do Alembic em que o banco fica, para orientar um rollback.
- Marcar o commit publicado com uma tag anotada `api-vX.Y.Z`, com título `api: resumo da versão` e a seção da versão no corpo:

  ```bash
  git tag -a api-vX.Y.Z
  git push origin api-vX.Y.Z
  ```

## [Não lançado]

Banco: revisão `0005` do Alembic.

### Adicionado

- Versão no caminho: todas as rotas ficam sob `/v1`. A documentação (`/docs`) e `GET /api/health` ficam fora da versão.
- Envelope único nas respostas de `/v1`, de sucesso e de erro: `{"sucesso", "mensagem", "dados"}`, com a lista `erros` nos erros de validação (`422`). Rota inexistente, método não permitido e erro interno também respondem nesse formato.
- Autenticação por e-mail e senha em `POST /v1/auth/login`, com token JWT e bloqueio temporário da conta após tentativas de login seguidas sem sucesso.
- Sessão do usuário: `GET /v1/auth/me`, `POST /v1/auth/renovar` e `POST /v1/auth/sair-de-todos`, que invalida todos os tokens já emitidos.
- Redefinição de senha por código enviado por e-mail: `POST /v1/auth/esqueci-senha` e `POST /v1/auth/redefinir-senha`.
- Primeiro acesso do aluno, separado da redefinição de senha: `POST /v1/auth/primeiro-acesso/codigo`, `POST /v1/auth/primeiro-acesso/validar-codigo` e `POST /v1/auth/primeiro-acesso/aluno`.
- Cadastro de aluno pela professora em `POST /v1/usuarios/alunos`, com envio do e-mail de acesso.
- Listagem de alunos para a professora em `GET /v1/usuarios/alunos`, paginada e com busca por nome ou e-mail que ignora maiúsculas e acentos. Mostra só quem concluiu o primeiro acesso.
- Detalhe do aluno em `GET /v1/usuarios/alunos/{id}`, com os dados do perfil e do responsável. Os campos `aulas` e `pagamentos` já existem na resposta, ainda sempre vazios.
- Perfil do próprio aluno em `GET /v1/auth/me/perfil` e edição em `PATCH /v1/auth/me/perfil`: nome, telefone e dados do responsável. E-mail, CPF do aluno e data de nascimento não são editáveis.
- Modelos e migrações de `usuario`, `codigo_verificacao` (`0001`) e `aluno` (`0002`), com campos de auditoria e soft delete.
- Migração `0003`, que habilita a extensão `unaccent` do PostgreSQL, usada na busca de alunos.
- Grupos de alunos para a professora em `/v1/grupos`: criar (só o título é obrigatório), listar, detalhar, editar e excluir. Os alunos entram na criação ou depois, em `POST /v1/grupos/{id}/alunos`, e saem em `DELETE /v1/grupos/{id}/alunos/{aluno_id}`. Um aluno pode estar em vários grupos.
- Tabela `professor` (migração `0004`), com CNPJ e chave Pix opcionais. As contas de professor que já existem ganham a linha correspondente na própria migração.
- Tabelas `grupo` e `grupo_aluno` (migração `0005`).
- Envio de e-mail com backend `console` (apenas loga) ou `smtp`.
- Script de criação da conta da professora: `python -m src.scripts.criar_professor`. Pergunta também o CNPJ (numérico ou alfanumérico) e a chave Pix, ambos opcionais.
- Script `aplicar_migracoes.sh`, para aplicar as migrações em produção ou homologação.
- Observabilidade com o Logfire, ligada pela variável `LOGFIRE_TOKEN`: requisições, consultas SQL, exceções e logs, sem enviar os dados recebidos nas rotas.
- Testes automatizados de autenticação, primeiro acesso, usuários, alunos, perfil, grupos e schemas.
- Documentação: guia de migrações com Alembic, variáveis de ambiente e comandos úteis.

### Alterado

- Dependências com versões fixas no `pyproject.toml`.
- Nome padrão dos bancos: `sgaa_dev` para desenvolvimento e `sgaa_test` para testes.

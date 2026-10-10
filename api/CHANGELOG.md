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

Banco: revisão `0002` do Alembic.

### Adicionado

- Autenticação por e-mail e senha em `POST /auth/login`, com token JWT e bloqueio temporário da conta após tentativas de login seguidas sem sucesso.
- Sessão do usuário: `GET /auth/me`, `POST /auth/renovar` e `POST /auth/sair-de-todos`, que invalida todos os tokens já emitidos.
- Redefinição de senha por código enviado por e-mail: `POST /auth/esqueci-senha` e `POST /auth/redefinir-senha`.
- Primeiro acesso do aluno, separado da redefinição de senha: `POST /auth/primeiro-acesso/codigo`, `POST /auth/primeiro-acesso/validar-codigo` e `POST /auth/primeiro-acesso/aluno`.
- Cadastro de aluno pela professora em `POST /usuarios/alunos`, com envio do e-mail de acesso.
- Modelos e migrações de `usuario`, `codigo_verificacao` (`0001`) e `aluno` (`0002`), com campos de auditoria e soft delete.
- Envio de e-mail com backend `console` (apenas loga) ou `smtp`.
- Script de criação da conta da professora: `python -m src.scripts.criar_professor`.
- Script `aplicar_migracoes.sh`, para aplicar as migrações em produção ou homologação.
- Testes automatizados de autenticação, primeiro acesso, usuários e schemas.
- Documentação: guia de migrações com Alembic, variáveis de ambiente e comandos úteis.

### Alterado

- Dependências com versões fixas no `pyproject.toml`.
- Nome padrão dos bancos: `sgaa_dev` para desenvolvimento e `sgaa_test` para testes.

# Migrações com Alembic

Guia dos comandos mais usados do Alembic neste projeto: criar uma migração, aplicá-la no banco, desfazê-la e o que fazer ao trocar de branch com migrações pendentes.

Todos os comandos devem ser executados dentro de `api/`, com o `.env` configurado (o Alembic usa a `DATABASE_URL` de lá — ver [Configuração da Máquina](../primeiros_passos/config_maquina.md)).

---

## 1. Conceitos rápidos

- **Migração (revision)**: arquivo em `alembic/versions/` com duas funções, `upgrade()` (aplica a mudança) e `downgrade()` (desfaz).
- **`revision` / `down_revision`**: cada migração aponta para a anterior, formando uma corrente. É isso que define a ordem, não o nome do arquivo.
- **`head`**: a última migração da corrente. **`base`**: o banco vazio, antes da primeira.
- **Tabela `alembic_version`**: fica no banco e guarda em qual migração ele está. O Alembic compara esse valor com os arquivos de `alembic/versions/`.

### Convenção do projeto

Os identificadores são sequenciais (`0001`, `0002`, ...) e o arquivo se chama `<id>_<descricao_curta>.py`, por exemplo `0001_usuario_e_codigo_verificacao.py`. Por isso, ao criar uma migração, informe sempre o `--rev-id`.

A numeração é **uma só para o projeto inteiro**, não por tabela: o id identifica a migração (um passo na história do banco), e uma mesma migração pode mexer em várias tabelas — a `0001` cria `usuario` e `codigo_verificacao`. A próxima será a `0002`, seja qual for a tabela alterada.

---

## 2. Resumo dos comandos

| O que eu quero | Comando |
| --- | --- |
| Ver em qual migração o banco está | `poetry run alembic current` |
| Ver o histórico de migrações | `poetry run alembic history --verbose` |
| Ver qual é a última migração do código | `poetry run alembic heads` |
| Saber se os modelos têm mudança sem migração | `poetry run alembic check` |
| Criar migração a partir dos modelos | `poetry run alembic revision --autogenerate --rev-id 0002 -m "descricao"` |
| Criar migração vazia (escrita à mão) | `poetry run alembic revision --rev-id 0002 -m "descricao"` |
| Aplicar todas as migrações pendentes | `poetry run alembic upgrade head` |
| Aplicar só a próxima | `poetry run alembic upgrade +1` |
| Desfazer a última | `poetry run alembic downgrade -1` |
| Ir para uma migração específica | `poetry run alembic upgrade 0002` / `poetry run alembic downgrade 0001` |
| Desfazer tudo (banco vazio) | `poetry run alembic downgrade base` |
| Ver o SQL sem executar | `poetry run alembic upgrade head --sql` |

---

## 3. Criar uma migração

1. Altere ou crie o modelo em `src/models/`. Se for um modelo novo, importe-o em `src/models/__init__.py` — o Alembic só enxerga os modelos registrados ali.

2. Garanta que o banco está atualizado antes de gerar (o autogenerate compara os modelos com o estado atual do banco):

   ```bash
   poetry run alembic upgrade head
   ```

3. Gere a migração, usando o próximo número da sequência:

   ```bash
   poetry run alembic revision --autogenerate --rev-id 0002 -m "adiciona tabela turma"
   ```

   Isso cria `alembic/versions/0002_adiciona_tabela_turma.py`.

4. **Revise o arquivo gerado.** O autogenerate é um ponto de partida, não um resultado final. Ele **não** detecta:

   - renomeação de tabela ou coluna (gera um `drop` + `create`, o que **apaga os dados**; troque por `op.rename_table` / `op.alter_column(..., new_column_name=...)`);
   - mudança nos valores de um `Enum` do PostgreSQL (escreva à mão: `op.execute("ALTER TYPE tipo_usuario_enum ADD VALUE 'novo_valor'")`);
   - remoção do tipo `Enum` no `downgrade` (após o `op.drop_table`, acrescente `sa.Enum(name="nome_do_enum").drop(op.get_bind())`);
   - migração de dados (preencher uma coluna nova, por exemplo).

5. Confira também o `downgrade()`: ele precisa desfazer exatamente o que o `upgrade()` fez, na ordem inversa.

> **Coluna `NOT NULL` em tabela que já tem dados:** informe um `server_default` ou faça em três passos (cria como `nullable`, preenche, altera para `NOT NULL`). Do contrário a migração falha no banco de quem já tem registros.

---

## 4. Persistir a migração no banco

```bash
poetry run alembic upgrade head
```

Depois confirme e teste o caminho de volta, para garantir que o `downgrade()` funciona:

```bash
poetry run alembic current        # deve mostrar o id novo seguido de (head)
poetry run alembic downgrade -1   # desfaz
poetry run alembic upgrade head   # aplica de novo
poetry run alembic check          # deve responder "No new upgrade operations detected."
```

Por fim, **faça o commit do arquivo da migração junto com a alteração do modelo**. Migração aplicada no seu banco e não commitada é a principal causa dos problemas da seção 6.

### Errei a migração. E agora?

- **Ainda não foi para o repositório remoto:** desfaça, corrija e reaplique.

  ```bash
  poetry run alembic downgrade -1
  # edite o arquivo (ou apague e gere de novo)
  poetry run alembic upgrade head
  ```

- **Já está no remoto / outras pessoas já aplicaram:** não edite a migração. Crie uma nova que corrija a anterior.

---

## 5. Atualizar o banco depois de um `git pull`

Sempre que o pull trouxer arquivos novos em `alembic/versions/`:

```bash
poetry run alembic upgrade head
```

Se a API ou os testes reclamarem de tabela ou coluna inexistente, quase sempre é isso.

---

## 6. Trocar de branch com migração aplicada

O banco local é um só e **não acompanha o `git checkout`**. Se você aplicou a migração `0003` na branch A e vai para a branch B, onde esse arquivo não existe, o banco continua na `0003` e qualquer comando do Alembic falha com:

```
Can't locate revision identified by '0003'
```

### O jeito certo: desfazer antes de trocar

1. Ainda na branch atual, descubra qual é a última migração que existe na branch de destino:

   ```bash
   git ls-tree --name-only nome-da-branch-destino alembic/versions/
   ```

2. Volte o banco até ela (ex.: o destino só tem até a `0002`):

   ```bash
   poetry run alembic downgrade 0002
   ```

3. Se a migração ainda não foi commitada, faça o commit (ou `git stash -u`). Arquivo não rastreado **vai junto** para a outra branch e o Alembic passaria a enxergá-lo lá.

4. Troque de branch e atualize:

   ```bash
   git checkout nome-da-branch-destino
   poetry run alembic upgrade head
   ```

Ao voltar para a branch original, basta `poetry run alembic upgrade head` de novo.

### Já troquei de branch e deu o erro

Volte para a branch onde a migração existe, faça o `downgrade` do passo 2 e troque de novo:

```bash
git checkout branch-original
poetry run alembic downgrade 0002
git checkout nome-da-branch-destino
poetry run alembic upgrade head
```

### A branch original não existe mais / perdi o arquivo

Sem o arquivo não há `downgrade()` para executar. Como é banco de desenvolvimento, o mais seguro é recriá-lo:

```bash
# apague e recrie o banco (psql, Docker, Supabase...) e então:
poetry run alembic upgrade head
poetry run python -m src.scripts.criar_professor
```

Existe também `poetry run alembic stamp --purge 0002`, que apenas **reescreve a tabela `alembic_version`** sem tocar no esquema. Use só se você desfizer manualmente as tabelas/colunas que sobraram; do contrário o banco fica diferente do que o Alembic acredita, e as próximas migrações falham com "já existe".

---

## 7. Duas pessoas criaram migração a partir da mesma base

Acontece quando duas branches criam, cada uma, a sua `0002` em cima da `0001`. Depois do merge, a corrente se bifurca e o `upgrade head` falha com:

```
Multiple head revisions are present for given argument 'head'
```

Com ids sequenciais, o sinal aparece antes: dois arquivos com o mesmo número em `alembic/versions/`.

Para resolver, **quem fez o merge por último reposiciona a própria migração no fim da fila**:

1. Antes de trazer a outra branch, desfaça a sua migração no banco local:

   ```bash
   poetry run alembic downgrade -1
   ```

2. Faça o merge/rebase e, no seu arquivo de migração:
   - renomeie o arquivo para o próximo número (`0002_...` → `0003_...`);
   - altere `revision = "0003"`;
   - altere `down_revision = "0002"` (a migração que veio da outra branch).

3. Confira e aplique:

   ```bash
   poetry run alembic heads          # deve listar apenas uma
   poetry run alembic upgrade head
   poetry run alembic check
   ```

Se as duas migrações mexem na mesma tabela ou coluna, revise o conteúdo: pode ser necessário gerar a sua novamente.

> O Alembic também oferece `alembic merge heads -m "..."`, que cria uma migração unindo as duas pontas. Preferimos reordenar, para manter o histórico linear e a numeração sequencial.

---

## 8. Erros comuns

| Mensagem | Causa | Solução |
| --- | --- | --- |
| `Can't locate revision identified by '...'` | O banco está em uma migração que não existe na branch atual. | Seção 6. |
| `Multiple head revisions are present` | Duas migrações com o mesmo `down_revision`. | Seção 7. |
| `Target database is not up to date.` | Tentou gerar migração com o banco atrasado. | `poetry run alembic upgrade head` e gere de novo. |
| Autogenerate criou migração vazia (`pass`) | Modelo novo não importado em `src/models/__init__.py`, ou não havia mudança. | Importe o modelo, apague o arquivo vazio e gere de novo. |
| `relation "..." already exists` | Esquema do banco e `alembic_version` fora de sincronia (uso de `stamp`, tabela criada à mão). | Recrie o banco de desenvolvimento e rode `upgrade head`. |
| `type "..._enum" already exists` | O `downgrade()` não removeu o tipo `Enum`. | Acrescente o `drop` do enum no `downgrade()` (seção 3). |

---

## 9. Cuidados

- **Os testes usam o banco da `DATABASE_URL`** e aplicam as migrações nele. Se o banco estiver em uma migração de outra branch, o `pytest` falha antes de rodar qualquer teste.
- **Nunca rode `downgrade` em banco de produção** sem ter certeza do que será apagado: remover coluna ou tabela apaga os dados.
- **Não edite migração que já foi para a `main`/`develop`.** Crie uma nova.
- Uma migração por mudança lógica, com descrição que diga o que ela faz (`adiciona tabela turma`, não `ajustes`).

# Deploy na AWS Lambda

A API roda na AWS Lambda, com o AWS SAM, em dois ambientes isolados: `homolog` e `prod`. O front web continua na Vercel e chama a API pela URL do CloudFront.

## Arquitetura

```
App / Web (Vercel) ──> CloudFront (plano Free + WAF) ──> Function URL ──> sgaa-api-<amb>  ──> Supabase (Transaction pooler)
EventBridge rate(5 minutes) ─────────────────────────────────────────────> sgaa-api-tarefa-<amb> ──> Supabase / Expo
As duas funções leem /<amb>/* do Parameter Store na partida
```

Cada ambiente é uma stack do CloudFormation, `sgaa-api-homolog` ou `sgaa-api-prod`, com:
- **`sgaa-api-<amb>`:** a API, com `lambda_handler.handler` (Mangum), 1024 MB, timeout de 15 s e Function URL pública.
- **`sgaa-api-tarefa-<amb>`:** a [tarefa agendada](notificacoes_push.md#tarefa-agendada), com `lambda_tarefa.handler`, 512 MB e timeout de 60 s. O EventBridge a chama a cada 5 minutos.
- **Log groups** `/sgaa/api-<amb>` e `/sgaa/api-tarefa-<amb>`, com retenção de 14 dias.
- **Distribuição do CloudFront** com a Function URL como origem, sem cache, repassando o `Authorization`, a query string e o corpo.
- **Roles das funções:** cada uma só lê o próprio prefixo do Parameter Store, então homolog não enxerga os segredos de prod.

Arquivos:

| Arquivo | Papel |
| --- | --- |
| `template.yaml` | Recursos da stack (SAM) |
| `samconfig.toml` | Nome da stack, região e prefixo no S3 de cada ambiente |
| `lambda_handler.py` / `lambda_tarefa.py` | Pontos de entrada da API e da tarefa |
| `src/core/parametros.py` | Lê o Parameter Store na partida |
| `src/core/origem.py` | Recusa com `403` o que não veio pelo CloudFront |
| `deploy_lambda.sh` | Monta o pacote, publica e limpa os pacotes antigos |
| `src/scripts/limpar_pacotes_deploy.py` | Deixa no S3 só os 5 pacotes mais recentes do ambiente |

## Custos

O objetivo é custo zero. A conta precisa estar no plano **Paid**: o Free fecha a conta em 6 meses. As cotas abaixo valem no Paid, sem prazo.

| Serviço | Uso | Cota gratuita |
| --- | --- | --- |
| Lambda | API + tarefa, nos dois ambientes | 1 milhão de requisições e 400 mil GB-s por mês, somando tudo |
| Tarefa agendada | ~8.700 execuções por mês por ambiente (a cada 5 min) | Cabe na cota da Lambda; a regra agendada do EventBridge não é cobrada por disparo |
| CloudFront (plano Free) | 1 distribuição por ambiente | US$ 0, 1 milhão de requisições e 100 GB por mês, sem cobrança de excedente; inclui o WAF e 5 GB de crédito de S3 |
| Parameter Store (Standard) | Leitura na partida | Sem custo na vazão padrão |
| KMS (`aws/ssm`) | Descriptografa as SecureString | Dentro da cota gratuita de requisições |
| CloudWatch Logs | Logs das funções | Cota gratuita de ingestão; retenção de 14 dias |
| S3 | Pacotes do deploy | Só os 5 últimos por ambiente, cobertos pelo crédito do CloudFront Free |

Para garantir, crie um **orçamento de custo zero** no Budgets, que avisa por e-mail no primeiro centavo.

## Parameter Store

Cada ambiente tem os parâmetros em `/<ambiente>/<nome>`, com o **nome do campo da configuração** (`src/core/config.py`), em minúsculas. Na partida, cada um vira uma variável de ambiente: `/prod/database_url` vira `DATABASE_URL`.

| Parâmetro | Tipo | Obrigatório | Valor |
| --- | --- | --- | --- |
| `database_url` | SecureString | Sim | URL do **Transaction pooler** do Supabase (porta 6543), com `postgresql+psycopg://` |
| `secret_key` | SecureString | Sim | 48+ caracteres aleatórios, diferente em cada ambiente |
| `cloudfront_segredo` | **String** | Sim | Valor aleatório, diferente em cada ambiente |
| `cors_origins` | String | Sim | Domínios do front na Vercel, separados por vírgula |
| `email_backend` | String | Sim | `smtp` |
| `email_remetente` | String | Sim | Ex.: `SGAA <nao-responda@dominio>` |
| `smtp_host`, `smtp_port`, `smtp_user` | String | Sim | Do provedor de e-mail |
| `smtp_password` | SecureString | Sim | Do provedor de e-mail |
| `push_backend` | String | Sim | `expo` |
| `expo_access_token` | SecureString | Se o projeto Expo exigir | Ver [Notificações Push](notificacoes_push.md#configuração) |
| `logfire_token` | SecureString | Não | Token de escrita do Logfire |
| `jwt_expira_dias`, `codigo_expira_minutos`, `convite_expira_horas` | String | Não | Só para mudar os padrões |

**Como criar cada parâmetro**, no console: *Systems Manager → Parameter Store → Create parameter*, na região `us-east-1`.
- **Name:** `/<ambiente>/<nome>`, em minúsculas, como `/homolog/database_url`.
- **Tier:** `Standard`.
- **Type:** o da tabela. Em SecureString, mantenha a chave padrão (`alias/aws/ssm`).
- **Value:** o valor. Em `cors_origins`, use o domínio sem `/` no fim, como `https://meu-front.vercel.app`. Em `smtp_port`, normalmente `587`.

Comece por homolog; prod pode ficar para quando for publicar lá. O nome de um parâmetro não pode ser editado: para renomear, crie outro com o mesmo valor e apague o antigo.

**Critério para o tipo:**
- segredo → **SecureString**;
- configuração → **String**;
- o que o template lê → **String**.
  - Hoje é só o `cloudfront_segredo`: o CloudFormation não resolve SecureString no cabeçalho do CloudFront e recusa o deploy.

**Variáveis definidas pelo template**, fora do Parameter Store:
- `SSM_PREFIXO` (`/homolog/` ou `/prod/`);
- `AMBIENTE` (`homolog` ou `prod`), que aparece em `/api/health` e no Logfire.

**Quando um parâmetro muda:**
- **Lido pela API:** vale nas instâncias novas. Para valer na hora, publique de novo ou mude a configuração da função no console.
- **`cloudfront_segredo`:** é lido no deploy, então exige um deploy novo.

Para gerar valores aleatórios: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Preparação da conta (uma vez)

1. **Conta:**
   - plano **Paid** (*Billing → Account plan*);
   -> Payment preferences (add cartão)

   - MFA no usuário root;
   -> My security credentials

   - orçamento de custo zero no Budgets.
   -> AWS Budgets
   -> Use a template → Zero spend budget
   -> Informe o email a receber a notificação


2. **Bucket dos pacotes:** `sgaa-api-deploy-<id-da-conta>`, na `us-east-1`, privado e sem versionamento.
   - copiar o ID da conta (12 digitos canto superior direito)
   - buscar por **S3** e clicar em **Create bucket**
      -> "general purpose"
      -> nome: 'sgaa-api-deploy-<id_da_conta>'
      -> região "us-east-1" (nao consegui mudar no meu)
      -> "block all public access" fica habilitado para ser um bucket privado
      -> "bucket versioning" deixe "disable"
      -> por fim, crie o bucket
   - guarde o nome do bucket pois vai ser uma variavel de ambiente emm `api/.aws.env`

3. **Usuários e permissões IAM.** Cada pessoa tem o próprio usuário, com login no console e chave de acesso próprios: nada de chave compartilhada. Quem sai do time tem só o seu usuário desativado.

   As permissões ficam em grupos, separando homologação de produção e limitadas aos recursos de cada ambiente. As políticas não ficam neste repositório, que é público: quem administra a conta cria os grupos e adiciona cada pessoa.

   Depois de ter o usuário, a pessoa entra, troca a senha, ativa o MFA e cria a própria chave:
   1. Clique no seu nome, no canto superior direito do console.
   2. Clique em *Security credentials*.
   3. Em *Access keys*, clique em *Create access key*.
   4. Escolha *Command Line Interface (CLI)*, avance e copie as duas chaves para o `api/.aws.env` (passo 4).

4. **`api/.aws.env`** (fora do Git):

   ```bash
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   SGAA_DEPLOY_BUCKET=sgaa-api-deploy-<id-da-conta>
   ```

5. **Parameter Store:** crie os parâmetros de cada ambiente. Confira neste mesmo arquivo a seção [Parameter Store](#parameter-store).

6. **Concorrência:** confira em *Service Quotas → Lambda → Concurrent executions*. Contas novas podem ter um limite baixo, e ele vale para a conta inteira, somando a API de homolog, a de prod e as tarefas agendadas. Acima do limite, a requisição é recusada com `429`. Um limite baixo costuma bastar para homolog; para prod, peça o aumento em *Request increase at account-level*, com antecedência, porque a AWS pode levar alguns dias para responder. O pedido é gratuito.

## Publicar (ainda não testado)

Requisitos na máquina: Docker e o Poetry, com o plugin `poetry-plugin-export`. O SAM roda na imagem oficial, sem instalação.

1. Se houver migração nova, aplique antes: `./aplicar_migracoes.sh`, com a URL do Session pooler do ambiente.
2. Rode `./deploy_lambda.sh homolog` ou `./deploy_lambda.sh prod`. O script:
   1. exige a árvore Git limpa e, para `prod`, a branch `main`;
   2. monta em `build/lambda` só o que a Lambda precisa, com o `requirements.txt` exportado do `poetry.lock`;
   3. roda `sam validate --lint`, `sam build` e `sam deploy`. Em prod, mostra as mudanças e pede confirmação;
   4. mostra as saídas da stack: `UrlApi`, `UrlFunction` e `DistribuicaoId`;
   5. apaga do S3 o que passar dos 5 pacotes e dos 5 templates mais recentes do ambiente.

## Depois do primeiro deploy de cada ambiente (console)

1. **CloudFront → Distribuição (`DistribuicaoId`) → Plano:** assine o plano **Free** (até 3 por conta).
2. **WAF da distribuição:** crie duas regras baseadas em taxa, por IP, numa janela de 5 minutos:
   - `/v1/auth/` (início do caminho): **100 requisições**;
   - todo o resto: **1.000 requisições**.

   Comece em modo **Count** por uma semana, veja os números nas métricas do WAF e passe para **Block**.
3. No front (Vercel), troque a URL da API pela `UrlApi`.
4. Depois que prod estiver no ar, remova o `vercel.json` da API e o projeto da API na Vercel.

## Rate limit e proteção

| Camada | O que faz |
| --- | --- |
| WAF do CloudFront | Bloqueia o IP que passa do limite. A requisição bloqueada não chega à Lambda nem conta na cota |
| Cabeçalho `X-Origem-Cloudfront` | Só o CloudFront chama a API: a Function URL chamada direto responde `403` |
| Concorrência da Lambda | Limita as execuções simultâneas e, com isso, o gasto máximo |
| Limites da API | Bloqueio de login após erros seguidos e limites dos códigos de verificação |
| Budgets | Avisa no primeiro centavo |

## Rollback

- Volte o código para o commit anterior e publique de novo. Para isso, use uma branch a partir dele; em prod, o script exige a `main`, então reverta o commit na `main`.
- Se a versão nova tinha migração, desfaça antes com `alembic downgrade`, pelo Session pooler. Ver [Migrações com Alembic](banco_de_dados/migracoes_alembic.md).

## Conferência depois do deploy

- Pela `UrlApi`:
  - `GET /api/health` mostra o `environment` do ambiente;
  - login, `GET /v1/auth/me` e uma listagem respondem normalmente.
- `GET <UrlFunction>api/health`, sem passar pelo CloudFront, responde `403`.
- O log group `/sgaa/api-tarefa-<amb>` mostra uma execução a cada 5 minutos, como `{"enviadas": 0, "recibos_conferidos": 0}`.
- *Billing → Bills* segue em US$ 0.

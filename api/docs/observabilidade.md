# Observabilidade

A API envia registros de execução ao [Pydantic Logfire](https://pydantic.dev/logfire), onde ficam consultáveis por 30 dias (plano gratuito). Na AWS Lambda os logs ficam 14 dias no CloudWatch, mas é pelo Logfire, com as consultas e as exceções ligadas a cada requisição, que se investiga um erro relatado depois.

A integração fica em `src/core/observabilidade.py` e é ligada pelo `index.py`.

## Quando está ligada

Só quando a variável `LOGFIRE_TOKEN` existe. Sem ela nada é configurado nem enviado: desenvolvimento local, testes e CI funcionam sem conta no Logfire.

| Ambiente | `LOGFIRE_TOKEN` | Campo `environment` no Logfire |
| --- | --- | --- |
| Produção (AWS Lambda) | Definida | `prod` |
| Homologação (AWS Lambda) | Definida | `homolog` |
| Local | Ausente; defina no `.env` só para testar a integração | `dev` |

O `environment` vem da variável `AMBIENTE`, definida pelo `template.yaml`. Sem ela, vale a `VERCEL_ENV`, da Vercel, e depois `dev`. A tarefa agendada (`lambda_tarefa.py`) também envia registros, com o mesmo `environment`, mas sem as requisições.

## O que é enviado

- **Requisições**: método, rota, status, duração, IP e user agent do cliente.
- **Consultas SQL**: o texto da consulta com os marcadores no lugar dos valores (`WHERE usuario.email = %(email_1)s`), e a duração.
- **Erros de validação (`422`)**: campo e tipo do erro. A mensagem não é enviada, porque pode citar o valor rejeitado.
- **Exceções**: tipo, mensagem e stack trace.
- **Logs do módulo `logging`** de nível `WARNING` para cima.

## O que não é enviado

- **Dados recebidos nas rotas**: corpo, argumentos e o valor rejeitado em um erro de validação. É o que impede e-mail, senha, CPF, telefone e códigos de chegarem ao Logfire.
- **Parâmetros das consultas SQL**.
- **Cabeçalhos**, incluindo o `Authorization`.

Como segunda barreira, atributos cujo nome contenha `senha`, `cpf`, `codigo`, `telefone` ou `token` são mascarados, além dos padrões em inglês que o Logfire já trata.

Dois cuidados ao escrever código novo:

- **Mensagens de log são enviadas como estão.** Não inclua dados pessoais nem segredos no texto de um `logger.warning(...)` ou `logger.exception(...)`; prefira identificadores, como `usuario_id`.
- **`EMAIL_BACKEND=console` loga o e-mail inteiro**, com destinatário e código de verificação. Em um ambiente com `LOGFIRE_TOKEN`, use `smtp`, ou aceite que os códigos ficarão visíveis no Logfire (tolerável apenas em homologação, com dados de teste).

## Serverless

Na AWS Lambda (e na Vercel) a instância pode ser congelada logo após responder. Por isso, quando a variável `AWS_LAMBDA_FUNCTION_NAME` (ou `VERCEL`) existe, um middleware envia os registros pendentes ao fim de cada requisição, com limite de 2 segundos. A tarefa agendada faz o mesmo ao fim de cada execução. Fora disso, o envio é em lote, em segundo plano.

## Configuração

1. No Logfire, criar um token de escrita no projeto `sgaa-api`.
2. Na Vercel, definir `LOGFIRE_TOKEN` em Production e em Preview (restrita à branch `develop`, para os previews de outras branches não consumirem a cota).
3. Fazer um novo deploy, pois variáveis de ambiente só valem para deploys criados depois.

Limites do plano gratuito: 10 milhões de registros por mês (ao atingir, o envio pausa, sem cobrança), 1 administrador e 2 convidados de leitura.

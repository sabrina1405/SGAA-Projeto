# Notificações Push

A API envia push para o app mobile (Expo) pelo [Expo Push Service](https://docs.expo.dev/push-notifications/sending-notifications/). O Expo entrega pelo FCM no Android e pelo APNs no iOS. A API não usa SDK nem credencial do Google: faz chamadas HTTPS com a `urllib` da biblioteca padrão.

As rotas e regras de negócio estão em [Fluxos da API](../../docs/api/fluxos.md#notificações-push).

## Custos e limites

- O Expo Push Service é gratuito, e o FCM também.
- O limite do Expo é de 600 notificações por segundo por projeto. Cada chamada leva até 100 mensagens.

## Como funciona

```
Feature (ex.: criar recado) ──> grava o recado + uma linha em `notificacao` (mesma transação)
        │
        └─ se já venceu, tenta enviar logo depois da requisição
Tarefa agendada (a cada 5 min) ──> envia as pendentes vencidas + confere os recibos do Expo
Envio: resolvedor do tipo ──> usuários ──> dispositivos ativos ──> Expo (lotes de 100)
```

**Fila (`notificacao`):** cada linha tem `tipo`, `referencia_id` (por exemplo, o id do recado) e `enviar_em`.
- Os destinatários e o texto são montados só na hora do envio. Um recado agendado respeita os grupos como estiverem no dia, e um recado excluído não é enviado.

**Envio:** `notificacao_service.processar_pendentes` pega uma notificação por vez com `FOR UPDATE SKIP LOCKED`. Assim, o envio imediato e a tarefa agendada nunca mandam a mesma notificação duas vezes.

**Falhas:** Expo fora do ar, 429 ou 5xx contam como uma tentativa.
- A próxima tentativa fica para 5, 10, 15… minutos depois.
- Depois de 5 tentativas, a notificação é abandonada.
- Os lotes que já saíram ficam registrados e não são repetidos.

**Recibos (`envio_push`):** cada mensagem gera um ticket.
- Depois de 15 minutos, a tarefa agendada consulta o recibo.
- `DeviceNotRegistered`, no ticket ou no recibo, desativa o dispositivo.
- O Expo guarda os recibos por 24 horas. Um envio sem recibo depois disso fica como `sem_recibo`.

**Envio imediato:** na requisição que cria o recado, o envio roda como `BackgroundTasks`. Na Lambda, com o Mangum, isso acontece antes de a resposta sair, e soma o tempo da chamada ao Expo, em geral menos de 1 segundo. Uma falha ali não afeta a requisição: fica para a tarefa agendada.

## Configuração

| Variável | Valor | Onde |
| --- | --- | --- |
| `PUSH_BACKEND` | `console` (padrão: só registra no log) ou `expo` | `.env` local; Parameter Store como String |
| `EXPO_ACCESS_TOKEN` | Access token do Expo, opcional | Parameter Store como SecureString |

O access token só é exigido se o projeto do Expo ativar o "Enhanced Security for Push Notifications", em *Project settings → Push notifications*. É recomendado em produção: sem ele, quem souber um token do aparelho consegue mandar push para ele.

Com `LOGFIRE_TOKEN` definido, o backend `console` envia ao Logfire o token do aparelho e o texto da notificação. Em homologação e produção, use `expo`.

## Tarefa agendada

- **Ponto de entrada:** `notificacao_service.executar_tarefa_agendada()`. Ela processa a fila e confere os recibos.
- **Localmente:** `poetry run python -m src.scripts.processar_notificacoes`.
- **Na AWS Lambda** (feito na branch do deploy):
  - `lambda_handler.handler` desvia para a tarefa quando o evento é `{"tarefa": "processar_notificacoes"}`. Os outros eventos seguem para o Mangum.
  - No `template.yaml`, um evento `Schedule` na função, com `rate(5 minutes)` e esse `Input`. São cerca de 8.700 invocações por mês, menos de 1% da cota gratuita da Lambda (1 milhão de requisições por mês). A regra agendada do EventBridge não é cobrada por disparo.
  - O intervalo é de 5 minutos por causa do lembrete de 30 minutos antes da aula: ele chega com até 5 minutos de atraso. Com 15 minutos, poderia chegar só 15 minutos antes da aula.
  - Não há rota pública nem segredo extra.

## Como adicionar um tipo novo de notificação

1. Acrescente o valor em `TipoNotificacao` (`src/models/notificacao.py`). O tipo é guardado como texto, então não precisa de migração.
2. No service da feature, escreva o resolvedor `conteudo_da_notificacao(sessao, referencia_id) -> Conteudo | None`, no molde de `recado_service.conteudo_da_notificacao`. Ele devolve os ids dos usuários, o título, o corpo e os `dados` do deep link. Devolve `None` quando a notificação não vale mais.
3. Registre o resolvedor em `_resolvedores()` (`src/services/notificacao_service.py`).
4. Na transação da feature, chame `notificacao_service.agendar(sessao, tipo, referencia_id, enviar_em)`. Se o horário puder mudar, use `reagendar`.
5. Para enviar logo após a requisição, adicione `notificacao_service.processar_pendentes_sem_falhar` como `BackgroundTasks` na rota.
6. Documente o tipo e o formato de `dados` em [Fluxos da API](../../docs/api/fluxos.md#notificações-push).

## O que o app precisa fazer

1. **Instalar** `expo-notifications` e configurar o plugin no `app.json`. O app precisa de um `projectId` do EAS (`eas init`).
2. **Android:**
   - criar um projeto no Firebase e baixar o `google-services.json` (fica no app);
   - gerar a chave da conta de serviço para o FCM V1 e enviá-la ao EAS, com `eas credentials` ou em *Project settings → Credentials*.
   - A API não usa nenhum desses arquivos.
3. **iOS:** a chave APNs é configurada pelo `eas credentials`. Exige conta Apple Developer.
4. **Depois do login:**
   - pedir permissão de notificação;
   - obter o token com `Notifications.getExpoPushTokenAsync({ projectId })`;
   - enviar `POST /v1/dispositivos` com `{"token": "...", "plataforma": "android"}`.
   - Repetir a cada login e quando o token mudar (`addPushTokenListener`).
5. **No logout:** chamar `DELETE /v1/dispositivos/{token}` antes de descartar o token de acesso. O token tem colchetes, então use `encodeURIComponent`.
6. **Ao tocar na notificação:** ler `notification.request.content.data`, por exemplo `{"tipo": "recado", "recado_id": 41}`, e abrir a tela correspondente.
7. **Para testar:** o push só funciona em aparelho físico. Use um development build: no Android, o Expo Go não recebe push remoto desde o SDK 53.

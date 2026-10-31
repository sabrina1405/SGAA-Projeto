# Fluxos e convenções da API

O que a API do SGAA espera além do que o Swagger mostra: as convenções comuns a todas as rotas, a ordem das chamadas em cada fluxo e os limites dos códigos de verificação.

A referência de cada rota (entrada, saída, campos e status) é o Swagger, em `/docs`, gerado a partir do código e sempre atualizado. Para acessá-lo localmente, ver [Iniciar Servidor Local](../../api/docs/primeiros_passos/iniciar_servidor_local.md).

- [Convenções](#convenções)
- [Fluxos](#fluxos)
- [Limites dos códigos](#limites-dos-códigos)

---

## Convenções

- Corpos de requisição e resposta em JSON.
- Campos desconhecidos no corpo são rejeitados com `422`.
- Rotas autenticadas exigem o cabeçalho `Authorization: Bearer <token>`.

### Versão

Todas as rotas da API ficam sob o prefixo `/v1`, por exemplo `POST /v1/auth/login`. Uma mudança incompatível em um recurso entra em uma versão nova (`/v2`), sem tirar a anterior do ar.

Ficam fora da versão a documentação (`/docs`, `/redoc`, `/openapi.json`) e a checagem de saúde (`GET /api/health`).

### Tokens

| Token | Como obter | Onde vale |
| --- | --- | --- |
| Token de acesso (`access_token`) | Login ou conclusão do primeiro acesso | Rotas autenticadas. Algumas exigem usuário do tipo `professor` ou `aluno`. |
| `token_primeiro_acesso` | Validação do código de primeiro acesso | Apenas no envio do formulário de primeiro acesso |

### Formato das respostas

Toda resposta das rotas `/v1`, de sucesso ou de erro, tem o mesmo envelope:

| Campo | Tipo | Conteúdo |
| --- | --- | --- |
| `sucesso` | booleano | `true` nas respostas `2xx` e `false` nas demais. |
| `mensagem` | texto | Resumo do resultado, pronto para exibir. |
| `dados` | objeto ou `null` | O recurso ou resultado da rota. `null` nos erros e nas rotas que não devolvem nada. |
| `erros` | lista | Só nos erros de validação (`422`): um item por campo recusado. |

O status HTTP continua indicando o resultado; `sucesso` apenas o repete no corpo.

```json
{
  "sucesso": true,
  "mensagem": "Aluno encontrado",
  "dados": { "id": 7, "nome_completo": "Maria Silva" }
}
```

```json
{ "sucesso": false, "mensagem": "Aluno não encontrado", "dados": null }
```

Erro de validação, para corpo ou parâmetro inválido:

```json
{
  "sucesso": false,
  "mensagem": "Dados inválidos",
  "dados": null,
  "erros": [
    { "local": ["body", "telefone"], "tipo": "string_pattern_mismatch", "mensagem": "..." }
  ]
}
```

- `local` indica onde está o campo: `["body", "campo"]` para o corpo, `["query", "campo"]` ou `["path", "campo"]` para parâmetros da URL.
- O valor enviado nunca é devolvido.

Erros comuns:

| Status | `mensagem` | Quando |
| --- | --- | --- |
| `401` | `Não autenticado` | Token ausente, malformado, expirado, invalidado ou do tipo errado para a rota. |
| `403` | `Sem permissão para esta ação` | Token válido, mas o tipo de usuário não pode usar a rota. |
| `404` | `Recurso não encontrado` | A rota não existe. Rotas que buscam um registro também respondem `404`, com mensagem própria, quando ele não existe ou foi removido. |
| `405` | `Método não permitido` | A rota existe, mas não aceita o método usado. |
| `500` | `Erro interno. Tente novamente em instantes.` | Falha inesperada no servidor. |

### Paginação

As listagens recebem os parâmetros `pagina` e `tamanho` e devolvem em `dados` o objeto `{"itens": [...], "total": N}`.

| Parâmetro | Valores | Padrão |
| --- | --- | --- |
| `pagina` | De 1 a 500 | 1 |
| `tamanho` | De 1 a 100 | 20 |

- `total` conta todos os registros que atendem ao filtro, não só os da página.
- Uma página além do fim responde `200` com `itens` vazio.

### Atualização parcial

Rotas `PATCH` alteram só os campos enviados; os demais ficam como estão.

- Corpo vazio gera `422`.
- Campo enviado como `null` gera `422`, exceto nos campos opcionais em que a rota aceita `null` para apagar o valor (hoje, a `descricao` do grupo).
- Se algum campo for recusado, nada é gravado.

---

## Fluxos

### Login

`POST /v1/auth/login` devolve o token de acesso.

- A resposta de erro é idêntica para e-mail inexistente, senha errada, conta sem senha e conta bloqueada.
- Após 5 senhas erradas seguidas, a conta fica bloqueada por 15 minutos.
- `POST /v1/auth/sair-de-todos` invalida todos os tokens do usuário, inclusive o usado na chamada.

### Primeiro acesso do aluno

| Passo | Quem | Rota | Resultado |
| --- | --- | --- | --- |
| 0 | Professor | `POST /v1/usuarios/alunos` | Conta criada sem senha; aluno recebe um código por e-mail (vale 72 h). |
| 1 | Aluno | `POST /v1/auth/primeiro-acesso/codigo` | Opcional: pede um código novo (vale 15 min) se o do convite expirou ou foi usado. |
| 2 | Aluno | `POST /v1/auth/primeiro-acesso/validar-codigo` | Código consumido; devolve `token_primeiro_acesso` (vale 30 min). |
| 3 | Aluno | `POST /v1/auth/primeiro-acesso/aluno` | Perfil e senha gravados; devolve o `access_token` (já entra logado). |

Enquanto o passo 3 não é concluído, a conta não tem senha: o login falha e a redefinição de senha não atende esse e-mail.

- **Passo 0**: se o envio do e-mail falhar (`502`), o cadastro é desfeito; basta repetir a chamada. O e-mail de um usuário removido continua reservado e gera `409`.
- **Passo 1**: responde `202` com a mesma mensagem exista ou não o e-mail. O código só é enviado para contas que ainda não concluíram o primeiro acesso.
- **Passo 2**: o código é consumido nessa chamada. Se o token expirar antes do envio do formulário, é preciso pedir um código novo. O `usuario.tipo` da resposta indica qual formulário exibir; hoje só existe o do aluno.
- **Passo 3**: a API calcula pela data de nascimento se o aluno tem responsável; não existe campo para informar isso. Para menor de 18, CPF e telefone são os do responsável. Um `409` (CPF já cadastrado) não invalida o token: basta corrigir e reenviar. Depois de concluído, o `token_primeiro_acesso` deixa de valer.

### Redefinição de senha

| Passo | Rota | Resultado |
| --- | --- | --- |
| 1 | `POST /v1/auth/esqueci-senha` | Código enviado por e-mail (vale 15 min). |
| 2 | `POST /v1/auth/redefinir-senha` | Senha trocada; todos os tokens anteriores deixam de valer. |

Só atende contas que já concluíram o primeiro acesso.

- **Passo 1**: responde `202` com a mesma mensagem exista ou não o e-mail, e mesmo que o envio falhe.
- **Passo 2**: a senha não pode ser igual ao e-mail. Em caso de sucesso, o bloqueio de login é removido.

### Alunos (professor)

| Rota | Resultado |
| --- | --- |
| `GET /v1/usuarios/alunos` | Lista paginada, em ordem alfabética, com `id`, `nome_completo`, `email` e `telefone`. |
| `GET /v1/usuarios/alunos/{id}` | Dados do aluno, perfil e responsável. |

- **Quem aparece na lista**: só alunos que concluíram o primeiro acesso. Um aluno cadastrado que ainda não ativou a conta não é listado; o detalhe dele responde pelo `id` devolvido no cadastro, com `perfil` nulo e `primeiro_acesso_concluido` falso.
- **Telefone da lista**: o do aluno ou, quando ele tem responsável, o do responsável.
- **Busca**: o parâmetro `busca` (até 100 caracteres) procura um trecho no nome ou no e-mail, sem diferenciar maiúsculas nem acentos: `joao` encontra `João`.
- **Detalhe**: `aulas` e `pagamentos` estão reservados e vêm sempre como listas vazias. Um `id` de professor responde `404`.

### Perfil do aluno

| Rota | Resultado |
| --- | --- |
| `GET /v1/auth/me/perfil` | Dados do aluno, perfil e responsável. |
| `PATCH /v1/auth/me/perfil` | Altera os campos enviados e devolve o perfil atualizado. |

`GET /v1/auth/me` continua devolvendo só os dados básicos da conta, para qualquer tipo de usuário.

Campos que o aluno pode editar:

| Campo | Aluno sem responsável | Aluno com responsável |
| --- | --- | --- |
| `nome_completo` | Sim | Sim |
| `telefone` | Sim | Não |
| `responsavel_nome`, `responsavel_cpf`, `responsavel_telefone` | Não | Sim |

- **Campo do outro grupo**: gera `422`, com um item em `erros` de `tipo` igual a `campo_nao_permitido` e `local` apontando o campo.
- **Campos bloqueados**: `email`, `cpf` e `data_nascimento` não são editáveis e geram `422`, como qualquer campo desconhecido.
- **Troca de responsável**: basta enviar os três campos `responsavel_*` na mesma chamada.
- **Quem tem responsável**: vale o que foi definido no primeiro acesso (`possui_responsavel`), não a idade atual. Um aluno que completa 18 anos continua editando os dados do responsável e ainda não tem como cadastrar CPF e telefone próprios.

### Grupos (professor)

| Rota | Resultado |
| --- | --- |
| `POST /v1/grupos` | Cria o grupo e devolve seus dados com a lista de alunos. |
| `GET /v1/grupos` | Lista paginada, por título, com `total_alunos` de cada grupo. |
| `GET /v1/grupos/{id}` | Dados do grupo e seus alunos, em ordem alfabética. |
| `PATCH /v1/grupos/{id}` | Altera `titulo` e/ou `descricao`. |
| `DELETE /v1/grupos/{id}` | Exclui o grupo. |
| `POST /v1/grupos/{id}/alunos` | Adiciona os alunos de `aluno_ids` e devolve o grupo atualizado. |
| `DELETE /v1/grupos/{id}/alunos/{aluno_id}` | Tira o aluno do grupo. |

- **Criação**: só `titulo` (até 50 caracteres) é obrigatório. `descricao` (até 100) e `aluno_ids` são opcionais; os alunos podem ser adicionados depois.
- **Dono do grupo**: cada professor vê e altera só os grupos que criou. Grupo de outro professor, inexistente ou excluído responde `404`.
- **Quem pode entrar**: alunos que concluíram o primeiro acesso, os mesmos da listagem de alunos. Um aluno pode estar em vários grupos.
- **`aluno_ids`**: até 100 ids por chamada, sem repetição. Se algum não for de um aluno válido, a resposta é `422` com `tipo` igual a `aluno_invalido`, a `mensagem` lista os ids recusados e nada é gravado: nenhum aluno entra e, na criação, o grupo não é criado.
- **Aluno que já está no grupo**: adicionar de novo é ignorado, sem erro.
- **Aluno que não está no grupo**: tentar removê-lo responde `404`.
- **Edição**: `descricao` enviada como `null` apaga a descrição; `titulo` não pode ser `null`.
- **Exclusão**: o grupo deixa de aparecer na listagem e no detalhe. Os alunos não são afetados.
- **Títulos repetidos** são permitidos.

### Recados (professor)

| Rota | Resultado |
| --- | --- |
| `GET /v1/recados/geral` | Recado geral do professor. `dados` vem `null` quando o painel está vazio. |
| `PUT /v1/recados/geral` | Cria ou substitui o recado geral com o `conteudo` enviado. |
| `DELETE /v1/recados/geral` | Limpa o painel. |
| `POST /v1/recados` | Cria o recado e devolve seus dados, com os alunos e grupos destinatários. |
| `GET /v1/recados` | Histórico paginado, do mais novo ao mais antigo, com `total_alunos` e `total_grupos` de cada recado. |
| `GET /v1/recados/{id}` | Dados do recado e seus destinatários. |
| `PATCH /v1/recados/{id}` | Altera só os campos enviados. |
| `DELETE /v1/recados/{id}` | Exclui o recado. |

- **Recado geral**: um por professor, sempre visível a todos os alunos. Limpar o painel já vazio não é erro.
- **Conteúdo**: texto em Markdown, de 1 a 5000 caracteres. O front faz a renderização. Espaços nas pontas são removidos e as quebras de linha são mantidas. Caracteres de controle, exceto quebra de linha e tabulação, geram `422`.
- **Período**: `data_inicio` (padrão: hoje, no horário de Brasília) e `data_fim` (opcional) no formato `AAAA-MM-DD`. Sem `data_fim`, o recado fica no mural até ser excluído. `data_fim` anterior a `data_inicio` gera `422` com `tipo` igual a `periodo_invalido`.
- **Destinatários**: `aluno_ids` e `grupo_ids` (até 100 ids cada, sem repetição) e os indicadores `todos_alunos` e `todos_grupos`. Os dois indicadores valem também para quem entrar depois do envio.
  - É preciso informar ao menos um destinatário. Do contrário, a resposta é `422` com `tipo` igual a `sem_destinatario`.
  - `todos_alunos` junto com `aluno_ids`, ou `todos_grupos` junto com `grupo_ids`, gera `422` com `tipo` igual a `destinatarios_conflitantes`.
  - Aluno que não concluiu o primeiro acesso gera `422` com `tipo` igual a `aluno_invalido`. Grupo de outro professor, inexistente ou excluído gera `422` com `tipo` igual a `grupo_invalido`. Em ambos os casos, nada é gravado.
- **Edição**: `data_fim` enviada como `null` tira a data de fim. Os outros campos não podem ser `null`. `aluno_ids` e `grupo_ids`, quando enviados, substituem os destinatários atuais. O período e os destinatários são conferidos com o recado completo, somando o que já está salvo ao que foi enviado.
- **Dono do recado**: cada professor vê e altera só os próprios recados. Recado de outro professor, inexistente ou excluído responde `404`.
- **Exclusão**: o recado sai do histórico e do mural.

### Mural (aluno)

| Rota | Resultado |
| --- | --- |
| `GET /v1/mural/geral` | Recados gerais preenchidos, com `professor_nome`, do mais recente ao mais antigo. |
| `GET /v1/mural` | Lista paginada dos recados destinados ao aluno no período de exibição, da `data_inicio` mais recente à mais antiga. |

- **Período**: o recado aparece de `data_inicio` até `data_fim`, inclusive, no horário de Brasília.
- **Quem vê**: o recado aparece para o aluno quando qualquer uma destas condições vale:
  - o recado é para todos os alunos;
  - o aluno está em `aluno_ids`;
  - o aluno está em um grupo de `grupo_ids`;
  - o recado é para todos os grupos e o aluno está em algum grupo do professor.
- **Grupos excluídos**: não contam. Um aluno que sai do grupo deixa de ver os recados enviados a esse grupo.

### Aulas (professor)

| Rota | Resultado |
| --- | --- |
| `POST /v1/aulas` | Cria a aula, ou todas as da série semanal, e devolve a primeira com os alunos e grupos. |
| `GET /v1/aulas?data_inicio=&data_fim=` | Aulas que começam no período, em ordem de início, com os alunos de cada uma. Filtros opcionais: `status`, `aluno_id` e `grupo_id`. |
| `GET /v1/aulas/{id}` | Dados da aula, com a participação de cada aluno e os grupos usados. |
| `PATCH /v1/aulas/{id}?escopo=` | Altera só os campos enviados. |
| `POST /v1/aulas/{id}/cancelar?escopo=` | Cancela a aula. |
| `POST /v1/aulas/{id}/alunos?escopo=` | Adiciona os alunos de `aluno_ids` e os dos grupos de `grupo_ids`. |
| `DELETE /v1/aulas/{id}/alunos/{aluno_id}?escopo=` | Tira o aluno da aula. |
| `GET /v1/aulas/reposicoes-pendentes` | Lista paginada dos alunos que ficaram sem aula, da aula mais antiga à mais nova. |
| `DELETE /v1/aulas/reposicoes-pendentes/{aula_id}/{aluno_id}` | Dispensa a reposição sem marcar aula. |

- **Horário**: `inicio` e `fim` no formato ISO 8601 com o fuso, como `2026-11-05T15:00:00-03:00`. Sem o fuso, a resposta é `422`. As respostas trazem sempre o horário de Brasília.
  - A aula precisa começar no futuro, terminar depois do início e durar no máximo 12 horas. Do contrário, `422` com `tipo` igual a `horario_invalido`.
- **Status**: `agendada` (o app mostra como "Confirmada"), `realizada` ou `cancelada`. A aula nasce `agendada`. O `PATCH` aceita `status` `realizada`, só depois de a aula começar, e `agendada`, para desfazer. O cancelamento tem rota própria.
- **Alunos**: `aluno_ids` e `grupo_ids` (até 100 ids cada, sem repetição). É preciso ao menos um aluno, direto ou por um grupo; do contrário, `422` com `tipo` igual a `sem_aluno`. Aluno ou grupo inválido gera `aluno_invalido` ou `grupo_invalido`, como nos recados, e nada é gravado.
  - Os alunos do grupo entram na aula na criação. Quem entrar no grupo depois não entra nas aulas já criadas, e quem sair continua nelas.
- **Repetição semanal**: com `repetir_semanalmente` igual a `true`, `repetir_ate` é obrigatório. São criadas aulas no mesmo dia da semana e horário, até essa data, inclusive, e por no máximo 26 semanas. As aulas da série têm o mesmo `serie_id`. `repetir_ate` sem `repetir_semanalmente`, faltando, anterior à primeira aula ou além de 26 semanas gera `422` com `tipo` igual a `repeticao_invalida`.
- **Conflito**: uma aula que se sobrepõe a outra aula não cancelada da professora gera `409`, com a aula em conflito na mensagem. Aulas encostadas (uma termina às 16h e a outra começa às 16h) não conflitam. Numa série, todas as aulas são conferidas, e nenhuma é criada se uma conflitar.
- **Escopo**: `esta` (padrão) ou `esta_e_seguintes`. O segundo alcança também as próximas aulas agendadas da mesma série; as canceladas e as realizadas ficam como estão. Em aula avulsa, os dois dão no mesmo.
- **Edição**: `descricao` e `anotacoes` enviadas como `null` são apagadas; os outros campos não podem ser `null`. Mudar `inicio` ou `fim` desloca as aulas do escopo pelo mesmo tanto e reconfere o conflito. Só uma aula agendada muda de horário. Aula cancelada não pode ser editada (`409`). `status` só vale com `escopo=esta` (do contrário, `422` com `tipo` igual a `escopo_invalido`).
- **Anotações**: notas da professora, até 5000 caracteres. O aluno não as vê.
- **Cancelamento**: só de aula agendada; de novo, `409`. `motivo` (até 150 caracteres) é opcional e aparece para o aluno. Com `repor` igual a `true`, cada aluno da aula fica com uma reposição pendente.
- **Reposição**: o aluno fica pendente quando cancela a participação ou quando a professora cancela com `repor`. Criar uma aula com `reposicao_de_aula_id` resolve a pendência dos alunos dessa aula que estiverem na nova. Aula de outra professora ou inexistente em `reposicao_de_aula_id` gera `422` com `tipo` igual a `aula_invalida`.
  - Cada item da lista traz `cancelada_por` (`aluno` ou `professor`) e o motivo correspondente.
- **Período da listagem**: `data_inicio` e `data_fim` (`AAAA-MM-DD`, horário de Brasília, inclusive) são obrigatórios e cobrem até 62 dias, o bastante para a visão mensal. Fora disso, `422` com `tipo` igual a `periodo_invalido`.
- **Dona da aula**: cada professora vê e altera só as próprias aulas. Aula de outra professora ou inexistente responde `404`.

### Agenda (aluno)

| Rota | Resultado |
| --- | --- |
| `GET /v1/agenda?data_inicio=&data_fim=` | Aulas do aluno que começam no período, em ordem de início, com `professor_nome` e a `participacao` dele. Filtro opcional: `status`. |
| `GET /v1/agenda/{aula_id}` | Uma aula da agenda. |
| `POST /v1/agenda/{aula_id}/cancelar` | Cancela a participação do aluno, com `motivo` opcional. |

- **O que aparece**: as aulas em que o aluno está, inclusive as canceladas e as que ele mesmo cancelou (`participacao` igual a `cancelada`). As anotações da professora não aparecem. O período segue a mesma regra da listagem da professora.
- **Cancelar**: só uma aula agendada que ainda não começou. A aula continua para os outros alunos, a professora recebe um push e o aluno entra na lista de reposições pendentes. Cancelar de novo, ou uma aula já cancelada ou começada, responde `409`. Aula em que o aluno não está responde `404`.

### Notificações push

| Rota | Resultado |
| --- | --- |
| `POST /v1/dispositivos` | Registra o `ExpoPushToken` do aparelho. Vale para professor e aluno. |
| `DELETE /v1/dispositivos/{token}` | Para de enviar push ao aparelho. |

- **Quando registrar**: depois do login, com `{"token": "ExponentPushToken[...]", "plataforma": "android"}`. `plataforma` é opcional (`android` ou `ios`). Registrar de novo o mesmo token não é erro; se o token estava com outro usuário (troca de conta no aparelho), ele passa para o usuário atual.
- **Quando remover**: no logout. Token desconhecido, de outro usuário ou já removido também responde `200`. `POST /v1/auth/sair-de-todos` remove todos os aparelhos do usuário.
- **Token inválido**: o Expo avisa quando um token deixa de valer (app desinstalado, por exemplo), e a API para de usá-lo. O app deve registrar o token a cada login, para recuperar esse caso.
- **Recado novo**: o aluno que vê o recado no mural recebe o push quando o recado entra no período de exibição. Na hora, se `data_inicio` é hoje ou já passou; às 7h (horário de Brasília) do dia de início, se é futura. Mudar `data_inicio` antes do envio muda o horário. Editar um recado já avisado não gera outro push, e um recado excluído antes do envio não é avisado.
- **Conteúdo**: o título é "Novo recado de {professor}" e o corpo traz o começo do texto, sem a marcação do Markdown.
- **Lembretes de aula**: os alunos com participação ativa recebem push 1 semana, 1 dia e 30 minutos antes de cada aula agendada. Lembretes cujo horário já passou na criação não são agendados: uma aula marcada para daqui a 2 dias só tem os de 1 dia e de 30 minutos. Mudar o horário refaz os lembretes. Aula cancelada, ou aluno que cancelou, não recebe lembrete. A tarefa agendada roda a cada 5 minutos, então um lembrete pode chegar até 5 minutos depois do horário.
  - Títulos: "Aula em 1 semana: {título}", "Aula amanhã: {título}" e "Aula em 30 minutos: {título}". O corpo traz o dia, o horário e a professora, como "qui, 24/09 às 15:00, com Ana".
- **Aula cancelada**: os alunos recebem um push na hora, se a aula ainda não começou. Ao cancelar a aula e as seguintes da série, vai um aviso só ("Aulas canceladas: {título}").
- **Aluno cancelou**: a professora recebe "{aluno} cancelou a aula", com a aula e o motivo.
- **`dados`**: cada push leva um objeto para o app abrir a tela certa ao tocar na notificação.
  - Recado: `{"tipo": "recado", "recado_id": 41}`.
  - Aula: `{"tipo": "aula_lembrete_semana", "aula_id": 501}`, com `tipo` igual a `aula_lembrete_semana`, `aula_lembrete_dia`, `aula_lembrete_30min`, `aula_cancelada` ou `aulas_canceladas`.
  - Aluno cancelou: `{"tipo": "participacao_cancelada", "aula_id": 501, "aluno_id": 866}`.

---

## Limites dos códigos

Valem para o primeiro acesso e para a redefinição de senha.

| Regra | Valor |
| --- | --- |
| Formato | 6 dígitos |
| Validade | 15 minutos (72 horas no código do convite) |
| Tentativas erradas por código | 5; depois disso o código deixa de valer |
| Intervalo mínimo entre pedidos | 60 segundos |
| Pedidos por hora | 5 |
| Código anterior | Deixa de valer quando um novo é emitido |

Pedidos acima do limite recebem a resposta normal (`202`), mas nenhum e-mail é enviado.

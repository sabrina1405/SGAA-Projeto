### Testes manuais no Postman

Corpos de requisição prontos para testar cada endpoint pelo Postman, com um caminho feliz e caminhos de erro. Ao lado de cada exemplo está o status esperado. O formato das respostas fica no Swagger (`/docs`), e as regras de negócio em [Fluxos da API](../../docs/api/fluxos.md).

Os endpoints sem parâmetros na URL e sem corpo aparecem só citados.

### Preparação

Variáveis sugeridas no ambiente do Postman:

| Variável | Valor |
| --- | --- |
| `base_url` | `http://localhost:8000/v1` |
| `token_professor` | `access_token` do login da professora |
| `token_aluno` | `access_token` do login de um aluno que concluiu o primeiro acesso |

Para obter o token, faça `POST {{base_url}}/auth/login` com o corpo abaixo e copie `dados.access_token`:

```json
{
  "email": "professora@exemplo.com",
  "senha": "sua-senha"
}
```

Em toda rota protegida, use na aba **Authorization** o tipo **Bearer Token**, com `{{token_professor}}` ou `{{token_aluno}}`.

- Sem token → `401`.
- Token do tipo errado (aluno em rota de professor, ou o contrário) → `403`.

Os ids dos exemplos (`866`, `131`, `41`…) são ilustrativos. Troque pelos ids do seu banco.

---

## Recados (professor)

Use `{{token_professor}}`.

Sem parâmetros e sem corpo:

- `GET {{base_url}}/recados/geral`: recado geral do professor.
- `DELETE {{base_url}}/recados/geral`: limpa o painel.

### PUT `{{base_url}}/recados/geral`

**Caminho feliz** → `200`

```json
{
  "conteudo": "Queridos alunos, **bem-vindos**!\n\nLink: meet.jit.si/ElCaminoIdiomas"
}
```

**Erro: conteúdo vazio** → `422`

```json
{
  "conteudo": "   "
}
```

**Erro: campo desconhecido** → `422`

```json
{
  "conteudo": "Bem-vindos!",
  "titulo": "Aviso"
}
```

### POST `{{base_url}}/recados`

**Caminho feliz: alunos e grupos escolhidos** → `201`

```json
{
  "conteudo": "Aula de sábado cancelada.",
  "data_inicio": "2026-10-25",
  "data_fim": "2026-10-31",
  "aluno_ids": [866],
  "grupo_ids": [131]
}
```

**Caminho feliz: todos os alunos, sem data de fim** → `201`

```json
{
  "conteudo": "Feriado na segunda.",
  "todos_alunos": true
}
```

**Caminho feliz: todos os grupos** → `201`

```json
{
  "conteudo": "Prova na próxima semana.",
  "todos_grupos": true
}
```

**Erro: nenhum destinatário** → `422`

```json
{
  "conteudo": "Aula de sábado cancelada."
}
```

**Erro: data de fim antes da de início** → `422`

```json
{
  "conteudo": "Aula de sábado cancelada.",
  "todos_alunos": true,
  "data_inicio": "2026-10-31",
  "data_fim": "2026-10-25"
}
```

**Erro: "todos" junto com ids avulsos** → `422`

```json
{
  "conteudo": "Aula de sábado cancelada.",
  "todos_alunos": true,
  "aluno_ids": [866]
}
```

**Erro: aluno inexistente ou que não concluiu o primeiro acesso** → `422`

```json
{
  "conteudo": "Aula de sábado cancelada.",
  "aluno_ids": [999]
}
```

**Erro: grupo de outro professor, inexistente ou excluído** → `422`

```json
{
  "conteudo": "Aula de sábado cancelada.",
  "grupo_ids": [999]
}
```

**Erro: data fora do formato `AAAA-MM-DD`** → `422`

```json
{
  "conteudo": "Aula de sábado cancelada.",
  "todos_alunos": true,
  "data_inicio": "31/10/2026"
}
```

### GET `{{base_url}}/recados?pagina=1&tamanho=20`

- Caminho feliz: `?pagina=1&tamanho=20` → `200`.
- Erro: `?pagina=0&tamanho=101` → `422`. `pagina` vai de 1 a 500 e `tamanho` de 1 a 100.

### GET `{{base_url}}/recados/{recado_id}`

- Caminho feliz: `/recados/41` → `200`.
- Erro: recado de outro professor, inexistente ou excluído, como `/recados/999` → `404`.
- Erro: id inválido, como `/recados/abc` ou `/recados/0` → `422`.

### PATCH `{{base_url}}/recados/{recado_id}`

URL de exemplo: `/recados/41`. Os erros de id da URL são os mesmos do `GET`.

**Caminho feliz: troca o texto, tira a data de fim e remove os alunos avulsos** → `200`. O recado precisa manter algum destinatário, como um grupo.

```json
{
  "conteudo": "Aula de sábado remarcada para domingo.",
  "data_fim": null,
  "aluno_ids": []
}
```

**Caminho feliz: passa a valer para todos os alunos** → `200`

```json
{
  "todos_alunos": true,
  "aluno_ids": [],
  "grupo_ids": []
}
```

**Erro: corpo vazio** → `422`

```json
{}
```

**Erro: campo obrigatório como `null`** → `422`

```json
{
  "conteudo": null
}
```

**Erro: data de fim antes da `data_inicio` já salva** → `422`

```json
{
  "data_fim": "2026-01-01"
}
```

**Erro: deixa o recado sem destinatário** → `422`. Vale para um recado que tinha só alunos avulsos.

```json
{
  "aluno_ids": []
}
```

### DELETE `{{base_url}}/recados/{recado_id}`

- Caminho feliz: `/recados/41` → `200`.
- Erro: o mesmo id de novo, já excluído → `404`.

---

## Mural (aluno)

Use `{{token_aluno}}`. Com o token da professora, a resposta é `403`.

Sem parâmetros e sem corpo:

- `GET {{base_url}}/mural/geral`: recados gerais preenchidos.

### GET `{{base_url}}/mural?pagina=1&tamanho=20`

- Caminho feliz: `?pagina=1&tamanho=20` → `200`.
- Erro: `?pagina=0` → `422`.

Para conferir quem vê cada recado:
1. Crie um recado com `data_inicio` no futuro. Ele não deve aparecer.
2. Crie um recado só com `aluno_ids` de outro aluno. Ele também não deve aparecer.
3. Tire o aluno do grupo destinatário (`DELETE /grupos/{id}/alunos/{aluno_id}`). O recado do grupo deve sumir do mural dele.

---

## Aulas (professor)

Use `{{token_professor}}`. Os horários levam o fuso, como `2026-11-05T15:00:00-03:00`. Nos exemplos, `501` é uma aula avulsa e `502` a primeira aula de uma série semanal.

Nas rotas que recebem `escopo` (`PATCH`, `cancelar` e `alunos`), o padrão é `esta`. Com `?escopo=esta_e_seguintes`, a ação vale também para as próximas aulas agendadas da série. Um valor fora desses dois, como `?escopo=todas`, gera `422`.

### POST `{{base_url}}/aulas`

**Caminho feliz: aula individual** → `201`

```json
{
  "titulo": "Espanhol",
  "descricao": "Aula individual",
  "inicio": "2026-11-05T15:00:00-03:00",
  "fim": "2026-11-05T16:00:00-03:00",
  "aluno_ids": [866]
}
```

**Caminho feliz: repetição semanal com um grupo** → `201`. Cria uma aula por terça até 15/12 e devolve a primeira.

```json
{
  "titulo": "Conversação",
  "inicio": "2026-11-03T18:00:00-03:00",
  "fim": "2026-11-03T19:00:00-03:00",
  "grupo_ids": [131],
  "repetir_semanalmente": true,
  "repetir_ate": "2026-12-15"
}
```

**Caminho feliz: reposição** → `201`. Resolve a reposição pendente dos alunos da aula `501` que estão nesta aula.

```json
{
  "titulo": "Espanhol (reposição)",
  "inicio": "2026-11-07T10:00:00-03:00",
  "fim": "2026-11-07T11:00:00-03:00",
  "aluno_ids": [866],
  "reposicao_de_aula_id": 501
}
```

**Erro: horário sem fuso** → `422`

```json
{
  "titulo": "Espanhol",
  "inicio": "2026-11-06T15:00:00",
  "fim": "2026-11-06T16:00:00",
  "aluno_ids": [866]
}
```

**Erro: fim antes do início** → `422`. O mesmo vale para uma aula com mais de 12 horas ou que começa no passado.

```json
{
  "titulo": "Espanhol",
  "inicio": "2026-11-06T16:00:00-03:00",
  "fim": "2026-11-06T15:00:00-03:00",
  "aluno_ids": [866]
}
```

**Erro: sem aluno nem grupo** → `422`. Um grupo sem alunos também gera esse erro.

```json
{
  "titulo": "Espanhol",
  "inicio": "2026-11-06T15:00:00-03:00",
  "fim": "2026-11-06T16:00:00-03:00"
}
```

**Erro: repetição sem `repetir_ate`** → `422`

```json
{
  "titulo": "Espanhol",
  "inicio": "2026-11-06T15:00:00-03:00",
  "fim": "2026-11-06T16:00:00-03:00",
  "aluno_ids": [866],
  "repetir_semanalmente": true
}
```

**Erro: repetição de mais de 26 semanas** → `422`

```json
{
  "titulo": "Espanhol",
  "inicio": "2026-11-06T15:00:00-03:00",
  "fim": "2026-11-06T16:00:00-03:00",
  "aluno_ids": [866],
  "repetir_semanalmente": true,
  "repetir_ate": "2027-12-31"
}
```

**Erro: aluno inexistente ou que não concluiu o primeiro acesso** → `422`

```json
{
  "titulo": "Espanhol",
  "inicio": "2026-11-06T15:00:00-03:00",
  "fim": "2026-11-06T16:00:00-03:00",
  "aluno_ids": [999999]
}
```

**Erro: horário sobreposto a outra aula da professora** → `409`. Basta repetir o primeiro exemplo com `"inicio": "2026-11-05T15:30:00-03:00"` e `"fim": "2026-11-05T16:30:00-03:00"`.

**Erro: `reposicao_de_aula_id` de outra professora ou inexistente** → `422`

### GET `{{base_url}}/aulas?data_inicio=2026-11-01&data_fim=2026-11-30`

- Caminho feliz: `?data_inicio=2026-11-01&data_fim=2026-11-30` → `200`. Visão do mês; para a semana ou o dia, use o mesmo formato com um período menor.
- Caminho feliz com filtros: `&status=agendada&aluno_id=866` ou `&grupo_id=131` → `200`.
- Erro: período de mais de 62 dias, como `?data_inicio=2026-11-01&data_fim=2027-01-31` → `422`.
- Erro: `data_fim` antes de `data_inicio` → `422`.
- Erro: sem `data_inicio` e `data_fim` → `422`.
- Erro: status desconhecido, como `&status=pendente` → `422`.

### GET `{{base_url}}/aulas/reposicoes-pendentes?pagina=1&tamanho=20`

- Caminho feliz: `?pagina=1&tamanho=20` → `200`.
- Erro: `?pagina=0` → `422`.

### DELETE `{{base_url}}/aulas/reposicoes-pendentes/{aula_id}/{aluno_id}`

- Caminho feliz: `/aulas/reposicoes-pendentes/501/866` → `200`.
- Erro: o mesmo de novo, já dispensado ou sem pendência → `404`.

### GET `{{base_url}}/aulas/{aula_id}`

- Caminho feliz: `/aulas/501` → `200`.
- Erro: aula de outra professora ou inexistente, como `/aulas/999999` → `404`.
- Erro: id inválido, como `/aulas/abc` → `422`.

### PATCH `{{base_url}}/aulas/{aula_id}?escopo=esta`

**Caminho feliz: título e anotações** → `200`

```json
{
  "titulo": "Espanhol avançado",
  "anotacoes": "Revisar o pretérito"
}
```

**Caminho feliz: muda o horário desta e das próximas aulas da série** (`/aulas/502?escopo=esta_e_seguintes`) → `200`. As seguintes são deslocadas pelo mesmo tanto, aqui 30 minutos.

```json
{
  "inicio": "2026-11-03T18:30:00-03:00",
  "fim": "2026-11-03T19:30:00-03:00"
}
```

**Caminho feliz: marca como realizada** → `200`. Só depois de a aula começar.

```json
{
  "status": "realizada"
}
```

**Erro: corpo vazio** → `422`

```json
{}
```

**Erro: realizada antes de a aula começar** → `422`. O mesmo corpo do caminho feliz, numa aula futura.

**Erro: status com `?escopo=esta_e_seguintes`** → `422`

```json
{
  "status": "agendada"
}
```

**Erro: novo horário sobreposto a outra aula** → `409`

```json
{
  "inicio": "2026-11-03T18:00:00-03:00",
  "fim": "2026-11-03T19:00:00-03:00"
}
```

**Erro: aula cancelada** → `409`

### POST `{{base_url}}/aulas/{aula_id}/cancelar?escopo=esta`

**Caminho feliz** → `200`. Os alunos recebem um push.

```json
{
  "motivo": "Imprevisto"
}
```

**Caminho feliz: série inteira a partir desta, com reposição** (`/aulas/502/cancelar?escopo=esta_e_seguintes`) → `200`. Cada aluno fica com uma reposição pendente.

```json
{
  "motivo": "Fim do semestre",
  "repor": true
}
```

**Erro: aula já cancelada** → `409`

```json
{}
```

### POST `{{base_url}}/aulas/{aula_id}/alunos?escopo=esta`

**Caminho feliz** → `200`. Quem já está na aula é ignorado.

```json
{
  "aluno_ids": [867],
  "grupo_ids": [131]
}
```

**Erro: nenhum aluno nem grupo** → `422`

```json
{}
```

### DELETE `{{base_url}}/aulas/{aula_id}/alunos/{aluno_id}?escopo=esta`

- Caminho feliz: `/aulas/501/alunos/867` → `200`.
- Erro: o mesmo de novo, aluno que não está na aula → `404`.

---

## Agenda (aluno)

Use `{{token_aluno}}`. Com o token da professora, a resposta é `403`.

### GET `{{base_url}}/agenda?data_inicio=2026-11-01&data_fim=2026-11-30`

- Caminho feliz: `?data_inicio=2026-11-01&data_fim=2026-11-30` → `200`. Aceita também `&status=cancelada`.
- Erro: período de mais de 62 dias → `422`.

### GET `{{base_url}}/agenda/{aula_id}`

- Caminho feliz: `/agenda/501` → `200`.
- Erro: aula em que o aluno não está ou inexistente, como `/agenda/999999` → `404`.

### POST `{{base_url}}/agenda/{aula_id}/cancelar`

**Caminho feliz** → `200`. A professora recebe um push e o aluno fica na lista de reposições pendentes. `motivo` é opcional.

```json
{
  "motivo": "Consulta médica"
}
```

**Erro: cancelar de novo** → `409`

```json
{}
```

**Erro: aula cancelada pela professora ou que já começou** → `409`

**Erro: aula em que o aluno não está** → `404`

---

## Arquivos

Vale para os dois tipos de usuário: use `{{token_professor}}` ou `{{token_aluno}}`. Sem token → `401`.

O arquivo sobe antes de salvar o formulário: abra a sessão, envie o conteúdo à `url_upload` e confirme. Com `DRIVE_BACKEND=desligado`, as rotas que falam com o Drive respondem `503`. Para testar de verdade, configure o [Google Drive](google_drive.md).

### POST `{{base_url}}/arquivos/sessao`

**Caminho feliz** → `201`. O campo `tamanho` é em bytes, até 5242880 (5 MB).

```json
{
  "nome": "apostila.pdf",
  "tipo_mime": "application/pdf",
  "tamanho": 1048576
}
```

**Erro: tipo não aceito** → `422`

```json
{
  "nome": "pagina.html",
  "tipo_mime": "text/html",
  "tamanho": 100
}
```

**Erro: acima de 5 MB** → `422`

```json
{
  "nome": "apostila.pdf",
  "tipo_mime": "application/pdf",
  "tamanho": 5242881
}
```

**Erro: sem o tamanho** → `422`

```json
{
  "nome": "apostila.pdf",
  "tipo_mime": "application/pdf"
}
```

- Erro: Drive desligado ou fora do ar → `503`.
- Erro: 10 arquivos enviados e ainda não salvos → `409`.

### Enviar o conteúdo

`PUT` na `url_upload` devolvida, com o arquivo no corpo (*Body → binary*) e o mesmo `Content-Type` da sessão, sem o token da API. A resposta do Google traz o `id`.

### POST `{{base_url}}/arquivos/{arquivo_id}/confirmar`

**Caminho feliz** → `200`. Repetir a chamada também responde `200`.

```json
{
  "drive_file_id": "1AbCdEfGhIjKlMnOp"
}
```

**Erro: arquivo que não existe no Drive ou é de outra sessão** → `422`

```json
{
  "drive_file_id": "naoexiste"
}
```

**Erro: id com caracteres inválidos** → `422`

```json
{
  "drive_file_id": "id/invalido"
}
```

- Erro: arquivo de outro usuário ou inexistente → `404`.
- Erro: Drive fora do ar → `503`.

### DELETE `{{base_url}}/arquivos/{arquivo_id}`

- Caminho feliz: `/arquivos/620` → `200`.
- Erro: o mesmo de novo, já descartado → `404`.
- Erro: arquivo já salvo em uma atividade ou entrega → `409`.

---

## Atividades (professor)

Use `{{token_professor}}`. Nos exemplos, `397` é uma atividade e `620` um arquivo confirmado.

### POST `{{base_url}}/atividades`

**Caminho feliz: alunos e grupos escolhidos, com anexo** → `201`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva **30 linhas**.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00-03:00",
  "permite_envio_arquivo": true,
  "aluno_ids": [866],
  "grupo_ids": [131],
  "arquivo_ids": [620]
}
```

**Caminho feliz: todos os alunos** → `201`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00-03:00",
  "todos_alunos": true
}
```

**Erro: sem destinatário** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00-03:00"
}
```

**Erro: todos os alunos junto com alunos avulsos** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00-03:00",
  "todos_alunos": true,
  "aluno_ids": [866]
}
```

**Erro: vencimento antes da liberação ou no passado** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-01T08:00:00-03:00",
  "todos_alunos": true
}
```

**Erro: data sem fuso** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00",
  "todos_alunos": true
}
```

**Erro: sem as datas** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "todos_alunos": true
}
```

**Erro: arquivo não confirmado, de outro usuário ou já usado** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00-03:00",
  "todos_alunos": true,
  "arquivo_ids": [999999]
}
```

**Erro: aluno inválido** → `422`

```json
{
  "titulo": "Redação",
  "descricao": "Escreva 30 linhas.",
  "liberar_em": "2026-11-03T08:00:00-03:00",
  "vence_em": "2026-11-20T23:59:00-03:00",
  "aluno_ids": [999999]
}
```

### GET `{{base_url}}/atividades?pagina=1&tamanho=20`

- Caminho feliz: `?pagina=1&tamanho=20` ou `?situacao=proximas` (`proximas` ou `vencidas`) → `200`.
- Erro: `?situacao=x` → `422`.
- Erro: `?pagina=0` → `422`.

### GET `{{base_url}}/atividades/entregas?pagina=1&tamanho=20`

- Caminho feliz: `?pagina=1&tamanho=20` ou `?situacao=entregues` (`proximas`, `vencidas` ou `entregues`) → `200`.
- Erro: `?situacao=x` → `422`.

### GET `{{base_url}}/atividades/{atividade_id}`

- Caminho feliz: `/atividades/397` → `200`.
- Erro: atividade de outro professor, inexistente ou excluída, como `/atividades/999999` → `404`.
- Erro: id inválido, como `/atividades/abc` → `422`.

### PATCH `{{base_url}}/atividades/{atividade_id}`

**Caminho feliz: título e vencimento** → `200`

```json
{
  "titulo": "Redação 2",
  "vence_em": "2026-11-25T23:59:00-03:00"
}
```

**Erro: corpo vazio** → `422`

```json
{}
```

**Erro: campo como `null`** → `422`

```json
{
  "titulo": null
}
```

**Erro: vencimento antes da liberação já salva** → `422`

```json
{
  "vence_em": "2026-11-01T08:00:00-03:00"
}
```

**Erro: deixa a atividade sem destinatário** → `422`

```json
{
  "aluno_ids": [],
  "grupo_ids": []
}
```

### DELETE `{{base_url}}/atividades/{atividade_id}`

- Caminho feliz: `/atividades/397` → `200`.
- Erro: o mesmo id de novo, já excluído → `404`.

### GET `{{base_url}}/atividades/{atividade_id}/entregas/{aluno_id}`

- Caminho feliz: `/atividades/397/entregas/866` → `200`.
- Erro: aluno que ainda não entregou → `404`.

---

## Minhas atividades (aluno)

Use `{{token_aluno}}`. Com o token da professora, a resposta é `403`.

### GET `{{base_url}}/minhas-atividades?pagina=1&tamanho=20`

- Caminho feliz: `?pagina=1&tamanho=20` ou `?situacao=realizadas` (`proximas`, `vencidas` ou `realizadas`) → `200`.
- Erro: `?situacao=x` → `422`.

### GET `{{base_url}}/minhas-atividades/{atividade_id}`

- Caminho feliz: `/minhas-atividades/397` → `200`.
- Erro: atividade ainda não liberada ou de que o aluno não é destinatário → `404`.

### PUT `{{base_url}}/minhas-atividades/{atividade_id}/entrega`

**Caminho feliz: com arquivo** → `200`. Depois do vencimento, a primeira entrega também responde `200`, com `status` igual a `entregue_com_atraso`.

```json
{
  "resposta": "Minha redação",
  "arquivo_ids": [623]
}
```

**Caminho feliz: edita o texto e mantém os arquivos** → `200`

```json
{
  "resposta": "Corrigida"
}
```

**Erro: resposta vazia** → `422`

```json
{
  "resposta": "   "
}
```

**Erro: sem a resposta** → `422`

```json
{}
```

**Erro: arquivo inválido** → `422`

```json
{
  "resposta": "Minha redação",
  "arquivo_ids": [999999]
}
```

**Erro: arquivo em uma atividade com o envio desligado** → `422`. O mesmo corpo do primeiro exemplo.

- Erro: editar depois do vencimento → `409`.
- Erro: atividade de que o aluno não é destinatário → `404`.

---

## Dispositivos (push)

Vale para os dois tipos de usuário: use `{{token_aluno}}` ou `{{token_professor}}`. Sem token → `401`.

Com `PUSH_BACKEND=console`, as notificações aparecem só no log do servidor. Para disparar uma, registre o token com o aluno e crie, com a professora, um recado para esse aluno com `data_inicio` de hoje. Para os recados agendados e os lembretes de aula, rode `poetry run python -m src.scripts.processar_notificacoes`. O cancelamento de uma aula, pela professora ou pelo aluno, avisa na hora.

### POST `{{base_url}}/dispositivos`

**Caminho feliz** → `200`. Registrar de novo o mesmo token também responde `200`.

```json
{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "plataforma": "android"
}
```

**Caminho feliz: sem a plataforma** → `200`

```json
{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
}
```

**Erro: token fora do formato do Expo** → `422`

```json
{
  "token": "abc123"
}
```

**Erro: plataforma desconhecida** → `422`

```json
{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "plataforma": "windows"
}
```

**Erro: sem o token** → `422`

```json
{}
```

### DELETE `{{base_url}}/dispositivos/{token}`

- Caminho feliz: `/dispositivos/ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]` → `200`. O Postman aceita os colchetes como estão; no app, use `encodeURIComponent`.
- Token desconhecido, de outro usuário ou já removido → também `200`, para o logout nunca falhar.
- Erro: token com mais de 255 caracteres → `422`.

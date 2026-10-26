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

## Dispositivos (push)

Vale para os dois tipos de usuário: use `{{token_aluno}}` ou `{{token_professor}}`. Sem token → `401`.

Com `PUSH_BACKEND=console`, as notificações aparecem só no log do servidor. Para disparar uma, registre o token com o aluno e crie, com a professora, um recado para esse aluno com `data_inicio` de hoje. Para os recados agendados, rode `poetry run python -m src.scripts.processar_notificacoes`.

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

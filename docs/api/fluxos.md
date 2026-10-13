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

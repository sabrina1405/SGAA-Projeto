# Rotas da API

Referência das rotas da API do SGAA: o que cada uma recebe, o que devolve e quais erros pode retornar. Para testar interativamente, use o Swagger em `/docs` com o servidor rodando (ver [Iniciar Servidor Local](../../api/docs/primeiros_passos/iniciar_servidor_local.md)).

- [Convenções](#convenções)
- [Fluxos](#fluxos)
- [Autenticação](#autenticação)
- [Primeiro acesso](#primeiro-acesso)
- [Redefinição de senha](#redefinição-de-senha)
- [Usuários](#usuários)
- [Utilitárias](#utilitárias)
- [Regras dos campos](#regras-dos-campos)
- [Objetos de resposta](#objetos-de-resposta)

---

## Convenções

- Corpos de requisição e resposta em JSON.
- Campos desconhecidos no corpo são rejeitados com `422`.
- Rotas autenticadas exigem o cabeçalho `Authorization: Bearer <token>`.

| Coluna "Auth" | Significado |
| --- | --- |
| — | Rota pública |
| Acesso | Token de acesso (`access_token`), de qualquer tipo de usuário |
| Professor | Token de acesso de um usuário do tipo `professor` |
| Primeiro acesso | `token_primeiro_acesso`, devolvido pela validação do código |

### Formato dos erros

| Status | Corpo | Quando |
| --- | --- | --- |
| `422` | `{"detail": [{"type": "...", "loc": ["body", "campo"], "msg": "..."}]}` | Corpo inválido. `loc` indica o campo; o valor enviado nunca é devolvido. |
| Demais | `{"detail": "mensagem"}` | Erros de regra de negócio, autenticação e permissão. |

Erros comuns a todas as rotas autenticadas:

| Status | `detail` | Quando |
| --- | --- | --- |
| `401` | `Não autenticado` | Token ausente, malformado, expirado, invalidado ou do tipo errado para a rota. |
| `403` | `Sem permissão para esta ação` | Token válido, mas o tipo de usuário não pode usar a rota. |

---

## Fluxos

### Primeiro acesso do aluno

| Passo | Quem | Rota | Resultado |
| --- | --- | --- | --- |
| 0 | Professor | `POST /usuarios/alunos` | Conta criada sem senha; aluno recebe um código por e-mail (vale 72 h). |
| 1 | Aluno | `POST /auth/primeiro-acesso/codigo` | Opcional: pede um código novo (vale 15 min) se o do convite expirou ou foi usado. |
| 2 | Aluno | `POST /auth/primeiro-acesso/validar-codigo` | Código consumido; devolve `token_primeiro_acesso` (vale 30 min). |
| 3 | Aluno | `POST /auth/primeiro-acesso/aluno` | Perfil e senha gravados; devolve o `access_token` (já entra logado). |

Enquanto o passo 3 não é concluído, a conta não tem senha: o login falha e a redefinição de senha não atende esse e-mail.

### Redefinição de senha

| Passo | Rota | Resultado |
| --- | --- | --- |
| 1 | `POST /auth/esqueci-senha` | Código enviado por e-mail (vale 15 min). |
| 2 | `POST /auth/redefinir-senha` | Senha trocada; todos os tokens anteriores deixam de valer. |

Só atende contas que já concluíram o primeiro acesso.

---

## Autenticação

| Rota | Auth | Entrada | Sucesso | Erros |
| --- | --- | --- | --- | --- |
| `POST /auth/login` | — | `email`, `senha` | `200` [TokenResposta](#tokenresposta) | `401` credenciais inválidas ou conta bloqueada · `422` |
| `GET /auth/me` | Acesso | — | `200` [UsuarioResposta](#usuarioresposta) | `401` |
| `POST /auth/renovar` | Acesso | — | `200` [TokenResposta](#tokenresposta) com validade cheia | `401` |
| `POST /auth/sair-de-todos` | Acesso | — | `204` sem corpo | `401` |

Observações:

- **Login**: a resposta de erro é idêntica para e-mail inexistente, senha errada, conta sem senha e conta bloqueada. Após 5 senhas erradas seguidas, a conta fica bloqueada por 15 minutos.
- **Sair de todos**: invalida todos os tokens do usuário, inclusive o usado na chamada.

---

## Primeiro acesso

| Rota | Auth | Entrada | Sucesso | Erros |
| --- | --- | --- | --- | --- |
| `POST /auth/primeiro-acesso/codigo` | — | `email` | `202` [MensagemResposta](#mensagemresposta) | `422` |
| `POST /auth/primeiro-acesso/validar-codigo` | — | `email`, `codigo` | `200` [TokenPrimeiroAcessoResposta](#tokenprimeiroacessoresposta) | `400` código inválido ou expirado · `422` |
| `POST /auth/primeiro-acesso/aluno` | Primeiro acesso | ver abaixo | `200` [TokenResposta](#tokenresposta) | `401` · `403` usuário não é aluno · `409` CPF já cadastrado · `422` |

### Corpo de `POST /auth/primeiro-acesso/aluno`

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `data_nascimento` | data (`AAAA-MM-DD`) | Sim | Define se o aluno é menor de idade. |
| `cpf` | texto | Sim | Do aluno, se maior de 18; do responsável, se menor. |
| `telefone` | texto | Sim | Do aluno, se maior de 18; do responsável, se menor. |
| `responsavel_nome` | texto | Só para menor de 18 | Nome completo do responsável. Enviar para maior de idade gera `422`. |
| `nova_senha` | texto | Sim | Ver [regras dos campos](#regras-dos-campos). |

Observações:

- **Pedido de código**: responde `202` com a mesma mensagem exista ou não o e-mail. O código só é enviado para contas que ainda não concluíram o primeiro acesso.
- **Validação do código**: o código é consumido nessa chamada. Se o token expirar antes do envio do formulário, é preciso pedir um código novo.
- **`usuario.tipo`** na resposta da validação indica qual formulário exibir. Hoje só existe o do aluno.
- **Responsável**: a API calcula pela data de nascimento se o aluno tem responsável; não existe campo para informar isso.
- **`409`** não invalida o token: basta corrigir o CPF e reenviar.
- Depois de concluído, o `token_primeiro_acesso` deixa de valer.

---

## Redefinição de senha

| Rota | Auth | Entrada | Sucesso | Erros |
| --- | --- | --- | --- | --- |
| `POST /auth/esqueci-senha` | — | `email` | `202` [MensagemResposta](#mensagemresposta) | `422` |
| `POST /auth/redefinir-senha` | — | `email`, `codigo`, `nova_senha` | `204` sem corpo | `400` código inválido ou expirado · `422` |

Observações:

- **Esqueci a senha**: responde `202` com a mesma mensagem exista ou não o e-mail, e mesmo que o envio falhe.
- **Redefinir**: a senha não pode ser igual ao e-mail. Em caso de sucesso, o bloqueio de login é removido e todos os tokens anteriores são invalidados.

### Limites dos códigos

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

---

## Usuários

| Rota | Auth | Entrada | Sucesso | Erros |
| --- | --- | --- | --- | --- |
| `POST /usuarios/alunos` | Professor | `nome_completo`, `email` | `201` [UsuarioResposta](#usuarioresposta) | `401` · `403` · `409` e-mail já cadastrado · `422` · `502` falha ao enviar o e-mail |

Observações:

- O aluno é criado sem senha e recebe por e-mail o código de primeiro acesso.
- **`502`**: o cadastro é desfeito; basta repetir a chamada.
- O e-mail de um usuário removido continua reservado e também gera `409`.

---

## Utilitárias

| Rota | Auth | Sucesso |
| --- | --- | --- |
| `GET /api/health` | — | `200` `{"status": "ok", "environment": "..."}` |
| `GET /docs` | — | Swagger |
| `GET /redoc` | — | ReDoc |

---

## Regras dos campos

| Campo | Regra | Normalização |
| --- | --- | --- |
| `email` | E-mail válido, até 80 caracteres | Espaços das pontas removidos; convertido para minúsculas |
| `nome_completo`, `responsavel_nome` | 3 a 100 caracteres, sem caracteres de controle | Espaços repetidos reduzidos a um |
| `senha` (login) | 1 a 128 caracteres | Nenhuma |
| `nova_senha` | 6 a 100 caracteres, com ao menos 1 minúscula, 1 maiúscula e 2 especiais | Nenhuma: vale exatamente o que foi digitado |
| `codigo` | Exatamente 6 dígitos | Espaços das pontas removidos |
| `cpf` | 11 dígitos com dígitos verificadores válidos | Aceita máscara (`123.456.789-09`); gravado só com dígitos |
| `telefone` | DDD + número, 10 ou 11 dígitos | Aceita máscara (`(11) 91234-5678`); gravado só com dígitos |
| `data_nascimento` | Anterior a hoje e de no máximo 120 anos atrás | — |

Caractere especial é qualquer um que não seja letra, dígito ou espaço.

---

## Objetos de resposta

### UsuarioResposta

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | inteiro | |
| `nome_completo` | texto | |
| `email` | texto | |
| `tipo` | texto | `aluno` ou `professor` |

### TokenResposta

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `access_token` | texto | JWT para o cabeçalho `Authorization` |
| `token_type` | texto | Sempre `bearer` |
| `expires_in` | inteiro | Validade em segundos (padrão: 30 dias) |
| `usuario` | [UsuarioResposta](#usuarioresposta) | |

### TokenPrimeiroAcessoResposta

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `token_primeiro_acesso` | texto | Só serve para enviar o formulário de primeiro acesso |
| `expires_in` | inteiro | Validade em segundos (30 minutos) |
| `usuario` | [UsuarioResposta](#usuarioresposta) | |

### MensagemResposta

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `mensagem` | texto | Texto para exibir ao usuário |

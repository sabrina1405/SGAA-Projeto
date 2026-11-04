# Google Drive

Os anexos de atividades e entregas ficam no Google Drive da conta do projeto. A API não recebe o arquivo: ela abre uma sessão de upload, o app envia direto ao Google e a API confere o resultado. Passando pela Lambda, 5 MB em base64 estourariam os 6 MB da Function URL.

As rotas e regras estão em [Fluxos da API](../../docs/api/fluxos.md#arquivos). A API não usa SDK: faz chamadas HTTPS com a `urllib`.

## Como funciona

```
App ──> POST /v1/arquivos/sessao ──> API valida e abre a sessão no Drive ──> devolve url_upload
App ──> PUT url_upload (conteúdo) ──> Google ──> devolve o id do arquivo
App ──> POST /v1/arquivos/{id}/confirmar ──> API confere o arquivo no Drive e cria o link
App ──> POST /v1/atividades ou PUT /v1/minhas-atividades/{id}/entrega, com arquivo_ids
```

- **Conferência:** a API só confia no que está no Drive. Ela verifica se o arquivo está na pasta do ambiente, se `appProperties.arquivo_id` bate e se o tamanho e o tipo são permitidos. Fora disso, responde `422` e a tarefa agendada apaga o arquivo.
- **Link:** quem tem o link abre o arquivo sem login. A API só o entrega a quem tem acesso à atividade.
- **Limpeza:** a tarefa agendada apaga até 20 arquivos por execução: os removidos, os `pendente` com mais de 1 hora e os confirmados sem vínculo há mais de 24 horas. Para na primeira falha do Drive e tenta de novo na próxima execução.
- **Sessão:** vale por uma semana. Quem guarda a URL pode enviar depois da limpeza e deixar um arquivo órfão na pasta. Exige um usuário autenticado e só ocupa espaço.

## Configuração (uma vez)

Faça tudo com a **conta Google do projeto**. O espaço gratuito é de 15 GB, divididos com o Gmail e o Fotos dessa conta.

1. No [Google Cloud Console](https://console.cloud.google.com/), crie um projeto e ative a **Google Drive API**.
2. Em *Google Auth Platform*, configure o público como **External** e adicione o escopo `.../auth/drive.file`, que é não sensível e só alcança os arquivos criados pelo app.
3. **Publique o app** (*Audience → Publish app*). Em modo de teste, o refresh token expira em 7 dias.
4. Em *Clients*, crie um cliente do tipo **Desktop app** e guarde o Client ID e o Client secret.
5. Gere o refresh token, **depois de publicar**:

   ```bash
   poetry run python -m src.scripts.gerar_token_drive
   ```

   Se o Google avisar que o app não foi verificado, siga por *Advanced*. O token não expira, salvo se for revogado ou ficar cerca de 6 meses sem uso.
6. Crie no Drive **uma pasta por ambiente**, como `sgaa-homolog` e `sgaa-prod`. O id da pasta é o final da URL dela. Elas precisam ser separadas, porque os ids dos arquivos se repetem entre os ambientes.
7. Coloque os parâmetros no [Parameter Store](deploy_aws_lambda.md#parameter-store), em cada ambiente.

| Variável | Valor | Tipo no Parameter Store |
| --- | --- | --- |
| `DRIVE_BACKEND` | `desligado` (padrão: as rotas respondem `503`) ou `google` | String |
| `GOOGLE_DRIVE_CLIENT_ID` | Client ID | String |
| `GOOGLE_DRIVE_CLIENT_SECRET` | Client secret | SecureString |
| `GOOGLE_DRIVE_REFRESH_TOKEN` | Refresh token | SecureString |
| `GOOGLE_DRIVE_PASTA_ID` | Id da pasta do ambiente | String |

## Validar com o Drive real

Os testes automáticos usam um Drive falso. Com as variáveis definidas, rode:

```bash
poetry run python -m src.scripts.validar_drive --origem http://localhost:8081
```

O script envia arquivos de teste e apaga tudo no fim. Confira:

1. **Envio normal:** o link abre em uma aba anônima, sem login.
2. **Envio maior que o declarado:** é recusado. Se não for, a confirmação da API ainda recusa acima de 5 MB.
3. **Envio pelo navegador:** o comando impresso, rodado no console de uma página da origem informada, mostra o id do arquivo. Erro de CORS significa que o envio direto não funciona na web.

## O que o app precisa fazer

1. Mandar o arquivo a `url_upload` com `PUT`, o conteúdo no corpo e o mesmo `Content-Type` da sessão. A resposta do Google traz o `id`.
2. Confirmar com esse `id` em `drive_file_id`. Em caso de `503` ou timeout, é seguro repetir.
3. Salvar o formulário com os `arquivo_ids`. Se o usuário desistir, chamar `DELETE /v1/arquivos/{id}`.

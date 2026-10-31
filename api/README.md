# API - SGAA

## 📚 Manuais e Documentação

Confira os guias passo a passo para configurar e rodar a aplicação:

- ⚙️ **[Configurações Iniciais da Máquina](docs/primeiros_passos/config_maquina.md)**: Pré-requisitos, instalação de dependências e configuração do arquivo `.env`.
- 🚀 **[Iniciar Servidor Local](docs/primeiros_passos/iniciar_servidor_local.md)**: Como rodar a API em modo de desenvolvimento e acessar a documentação do Swagger.
- 🛠️ **[Comandos Úteis e Scripts](scripts.md)**: Lista de comandos para testes, linters e utilitários.
- 🗄️ **[Migrações com Alembic](docs/banco_de_dados/migracoes_alembic.md)**: Como criar, aplicar e desfazer migrações, e o que fazer ao trocar de branch.
- 🔭 **[Observabilidade](docs/observabilidade.md)**: O que a API envia ao Logfire, o que fica de fora e como configurar o token.
- 🛡️ **[Auditoria de Dependências](docs/auditoria_dependencias.md)**: Como usar o `pip-audit` para checar vulnerabilidades conhecidas antes de instalar um pacote e no `requirements.txt`.
- 🔌 **[Fluxos e Convenções da API](../docs/api/fluxos.md)**: Convenções das rotas, fluxos de login, primeiro acesso e redefinição de senha, e limites dos códigos. A referência de cada rota é o Swagger, em `/docs`.
- 🔔 **[Notificações Push](docs/notificacoes_push.md)**: Como o envio pelo Expo funciona, a tarefa agendada, como adicionar um tipo novo de notificação e o que o app precisa fazer.
- ☁️ **[Deploy na AWS Lambda](docs/deploy_aws_lambda.md)**: Arquitetura, custos, parâmetros do Parameter Store, preparação da conta, como publicar e rate limit.
- 📮 **[Testes no Postman](docs/postman.md)**: Corpos de requisição prontos, com caminho feliz e de erro e o status esperado, de cada endpoint com parâmetros ou corpo.

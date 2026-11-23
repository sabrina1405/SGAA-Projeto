## Comandos

1. Instalar dependências - `npm install`

2. Iniciar o app - `npx expo start`

3. Resetar o 'placeholder' do projeto inicial - `npm run reset-project`

Para mais comandos, confira o arquivo `package.json`

## Links importantes

- https://expo.dev/ (Infra para build pelo CLI, CI/CD pra mobile, deploy e monitoramento de produção )
- (https://docs.expo.dev/develop/unit-testing/)

## Observações/Tarefas a fazer

- versão do expo

a versão do expo hoje no projeto é ("expo": "~57.0.26") porem para testes no expo go pelo celular foi necessário realizar um downgrade para a versão ("expo": "54.0.0"), o que impactou diretamente nas versões de várias outras dependências, que tiveram que mudar também. 

preferível ajustar essa questão o mais cedo possível para que seja viável os testes pelo app `Expo GO` no celular.

- garantia de qualidade (https://docs.expo.dev/guides/using-eslint/)
   - do código com eslint 
   - de estilo do código com prettier

embora o estilo possa ser algo ignorado, a qualidade é um ponto importante a ser investido em sistemas que vão para produção. mas como a documentação oferece também um manual de configuração pra isso, seria interessante realizar os dois.

- lock de versões

para nos protegermos de possíveis vulnerabilidades, é importante travar a versão dos pacotes que usamos ao longo do projeto. para isso não basta só eliminar o `~` ou `^`, é necessário investir um tempo pesquisando as libs e vendo se há ou não alguma vulnerabilidade crítica para dada versão.

é possível apenas realizar esse ajuste nas dependências que vão a produção, então as `devDependencies` podem ser ignoradas desse ajuste.

recomendo demais não usar IA para esse ponto, visto que a mesma tem suas limitações para informações mais recentes.

- separação de ambiente de homologação e produção (variaveis de ambiente)

- definição de arquivo para injetar a URL das chamadas a API segundo o ambiente (dev ou não dev)

- env.example

- manual para
    - instalar, configurar
    - rodar localmente

- testes automatizados (um bonus, não tão necessário)

seria interessante estar utilizando testes automatizados para garantir que não esta tendo regressão sem precisar testar todas as telas do sistema.
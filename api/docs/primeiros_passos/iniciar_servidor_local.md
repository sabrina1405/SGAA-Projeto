# Iniciar o Servidor Local

Este documento descreve como iniciar a API em ambiente de desenvolvimento local.

---

## Pré-requisito

Certifique-se de que concluiu os passos descritos em [Configuração da Máquina](config_maquina.md) (instalação de dependências e arquivo `.env` configurado).

---

## Como Iniciar a Aplicação

Navegue até o diretório `api/` e execute o comando abaixo:

```bash
cd api
poetry run uvicorn index:app --reload
```

A API estará acessível em: `http://localhost:8000`

---

## Documentação Interativa (Swagger / Redoc)

Com o servidor rodando, você pode acessar a documentação gerada automaticamente pelo FastAPI:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Executar para Testes em Dispositivos Móveis / Rede Local

Se você precisar acessar a API através do seu celular ou outro dispositivo na mesma rede local:

```bash
poetry run uvicorn index:app --host 0.0.0.0 --port 8000 --reload
```

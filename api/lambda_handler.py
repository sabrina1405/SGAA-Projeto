"""Ponto de entrada da API na AWS Lambda, chamado pela Function URL (atrás do
CloudFront)."""

from src.core.parametros import carregar_parametros

# Antes de importar a aplicação, que lê a configuração ao ser importada.
carregar_parametros()

from mangum import Mangum

from index import app

handler = Mangum(app, lifespan="off")

import os
import sys
from pathlib import Path

# Garante que o diretório raiz e o diretório atual estejam no PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import obter_config
from src.core.observabilidade import configurar_observabilidade
from src.core.origem import ExigirCloudFront
from src.main import app as src_app

# AMBIENTE vem do template da AWS (homolog ou prod); VERCEL_ENV, da Vercel.
ENVIRONMENT = os.getenv("AMBIENTE") or os.getenv("VERCEL_ENV", "dev")

# A documentação (/docs, /redoc) é servida pela aplicação montada em "/", que é onde ficam as rotas; a daqui a esconderia.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=obter_config().lista_cors_origins,
    # A autenticação usa token Bearer no header, sem cookies.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

cloudfront_segredo = obter_config().cloudfront_segredo
if cloudfront_segredo is not None:
    # Adicionado por último, fica por fora do CORS e barra antes de tudo.
    app.add_middleware(ExigirCloudFront, segredo=cloudfront_segredo.get_secret_value())


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": ENVIRONMENT}


configurar_observabilidade(src_app, app, ENVIRONMENT)

app.mount("/", src_app)

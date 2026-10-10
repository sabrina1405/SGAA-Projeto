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
from src.main import app as src_app

ENVIRONMENT = os.getenv("VERCEL_ENV", "dev")

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


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": ENVIRONMENT}


app.mount("/", src_app)

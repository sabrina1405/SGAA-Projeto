import os
import sys
from pathlib import Path

# Garante que o diretório raiz e o diretório atual estejam no PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.main import app as src_app

ENVIRONMENT = os.getenv("VERCEL_ENV", "dev")

app = FastAPI(
    title="SGAA API",
    description="Backend do Sistema de Gerenciamento de Alunos e Aulas",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": ENVIRONMENT}


app.mount("/", src_app)

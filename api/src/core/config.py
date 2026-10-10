from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_API = Path(__file__).resolve().parents[2]


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=RAIZ_API / ".env", extra="ignore")

    database_url: str
    secret_key: SecretStr = Field(min_length=32)

    jwt_expira_dias: int = Field(default=30, gt=0)
    codigo_expira_minutos: int = Field(default=15, gt=0)
    convite_expira_horas: int = Field(default=72, gt=0)

    email_backend: Literal["console", "smtp"] = "console"
    email_remetente: str = "SGAA <nao-responda@localhost>"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")

    # Origens separadas por vírgula. O app mobile não depende de CORS.
    cors_origins: str = "http://localhost:8081"

    @property
    def lista_cors_origins(self) -> list[str]:
        return [
            origem.strip() for origem in self.cors_origins.split(",") if origem.strip()
        ]


@lru_cache
def obter_config() -> Config:
    return Config()

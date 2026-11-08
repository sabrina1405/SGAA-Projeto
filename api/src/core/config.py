from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_API = Path(__file__).resolve().parents[2]


AMBIENTES_AWS = {"homolog", "prod"}


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=RAIZ_API / ".env", extra="ignore")

    # AMBIENTE vem do template da AWS (homolog ou prod); VERCEL_ENV, da Vercel.
    ambiente: str | None = None
    vercel_env: str | None = None

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

    # "expo" envia pelo Expo Push Service; "console" só registra no log.
    push_backend: Literal["console", "expo"] = "console"
    # Access token do Expo, exigido quando o projeto ativa o envio com segurança reforçada.
    expo_access_token: SecretStr | None = None

    # "google" guarda os arquivos no Drive; "desligado" responde 503 nas rotas.
    drive_backend: Literal["desligado", "google"] = "desligado"
    google_drive_client_id: str = ""
    google_drive_client_secret: SecretStr | None = None
    google_drive_refresh_token: SecretStr | None = None
    # Uma pasta por ambiente: os ids de arquivo se repetem entre eles.
    google_drive_pasta_id: str = ""

    # Token de escrita do Logfire. Sem ele, a observabilidade fica desligada.
    logfire_token: SecretStr | None = None

    # Na AWS: valor que o CloudFront envia no cabeçalho X-Origem-Cloudfront.
    # Com ele definido, a API recusa as chamadas que não passaram pelo CloudFront.
    cloudfront_segredo: SecretStr | None = None

    # Origens separadas por vírgula. O app mobile não depende de CORS.
    cors_origins: str = "http://localhost:8081"

    @model_validator(mode="after")
    def conferir_ambiente_publicado(self) -> Self:
        """Falha ao subir em vez de publicar a API com uma configuração insegura."""
        na_aws = self.ambiente in AMBIENTES_AWS
        if na_aws and self.cloudfront_segredo is None:
            # Sem o segredo, a Function URL aceitaria chamadas fora do CloudFront.
            raise ValueError(f"CLOUDFRONT_SEGREDO é obrigatório em {self.ambiente}")
        publicado = na_aws or self.vercel_env == "production"
        if publicado and self.email_backend == "console":
            # O backend console grava os códigos de verificação no log.
            raise ValueError("EMAIL_BACKEND=console não é permitido fora de dev")
        return self

    @property
    def lista_cors_origins(self) -> list[str]:
        return [
            origem.strip() for origem in self.cors_origins.split(",") if origem.strip()
        ]


@lru_cache
def obter_config() -> Config:
    return Config()

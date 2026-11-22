import pytest
from pydantic import ValidationError

from src.core.config import Config

SEGURA = {"cloudfront_segredo": "segredo", "email_backend": "smtp"}


def _config(**campos):
    return Config(_env_file=None, **campos)


@pytest.mark.parametrize("ambiente", ["homolog", "prod"])
def test_aws_exige_o_segredo_do_cloudfront(ambiente):
    with pytest.raises(ValidationError, match="CLOUDFRONT_SEGREDO"):
        _config(ambiente=ambiente, email_backend="smtp")


@pytest.mark.parametrize(
    "campos",
    [
        {"ambiente": "homolog", "cloudfront_segredo": "segredo"},
        {"ambiente": "prod", "cloudfront_segredo": "segredo"},
        {"vercel_env": "production"},
    ],
)
def test_ambiente_publicado_recusa_o_email_no_console(campos):
    with pytest.raises(ValidationError, match="EMAIL_BACKEND"):
        _config(email_backend="console", **campos)


@pytest.mark.parametrize(
    "campos",
    [
        {},
        {"ambiente": "dev"},
        {"vercel_env": "preview"},
        {"ambiente": "prod", **SEGURA},
        {"vercel_env": "production", "email_backend": "smtp"},
    ],
)
def test_configuracoes_aceitas(campos):
    _config(**campos)

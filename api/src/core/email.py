import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from src.core.config import obter_config

logger = logging.getLogger(__name__)

TIMEOUT_SMTP_SEGUNDOS = 10


class EnviadorEmail(Protocol):
    def enviar(self, para: str, assunto: str, corpo: str) -> None: ...


class EnviadorEmailConsole:
    """Apenas registra a mensagem no log. Para desenvolvimento e testes."""

    def enviar(self, para: str, assunto: str, corpo: str) -> None:
        logger.warning("E-mail para %s | %s\n%s", para, assunto, corpo)


class EnviadorEmailSmtp:
    def enviar(self, para: str, assunto: str, corpo: str) -> None:
        config = obter_config()
        mensagem = EmailMessage()
        mensagem["From"] = config.email_remetente
        mensagem["To"] = para
        mensagem["Subject"] = assunto
        mensagem.set_content(corpo)

        with smtplib.SMTP(
            config.smtp_host, config.smtp_port, timeout=TIMEOUT_SMTP_SEGUNDOS
        ) as servidor:
            servidor.starttls()
            if config.smtp_user:
                servidor.login(
                    config.smtp_user, config.smtp_password.get_secret_value()
                )
            servidor.send_message(mensagem)


def obter_enviador_email() -> EnviadorEmail:
    if obter_config().email_backend == "smtp":
        return EnviadorEmailSmtp()
    return EnviadorEmailConsole()

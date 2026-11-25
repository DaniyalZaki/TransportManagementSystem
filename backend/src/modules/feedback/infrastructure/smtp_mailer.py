import asyncio
import smtplib
from email.message import EmailMessage

from src.infrastructure.configuration.settings import Settings
from src.modules.feedback.domain.models import FeedbackSubmission


class SmtpFeedbackMailer:
    def __init__(self, settings: Settings) -> None: self._settings = settings

    async def send(self, item: FeedbackSubmission) -> None:
        await asyncio.to_thread(self._send, item)

    def _send(self, item: FeedbackSubmission) -> None:
        if not self._settings.smtp_host or not self._settings.feedback_recipient:
            raise RuntimeError("Feedback SMTP is not configured")
        message = EmailMessage()
        message["Subject"] = "Transport Service feedback"
        message["From"] = self._settings.smtp_sender or self._settings.feedback_recipient
        message["To"] = self._settings.feedback_recipient
        message.set_content(f"Feedback:\n{item.content}\n\nName: {item.name or 'Anonymous'}\nContact: {item.contact or 'Not provided'}")
        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=10) as client:
            if self._settings.smtp_username:
                client.starttls()
                client.login(self._settings.smtp_username, self._settings.smtp_password or "")
            client.send_message(message)

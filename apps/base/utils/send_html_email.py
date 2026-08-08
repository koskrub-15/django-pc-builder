"""Shared sender for the site's transactional email."""

import logging
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_html_email(
    subject: str,
    template_name: str,
    context: dict[str, Any],
    recipients: list[str],
    reply_to: list[str] | None = None,
) -> bool:
    """Render a template and mail it, reporting whether delivery succeeded.

    Delivery failures are logged and swallowed: every caller runs inside a
    request that should still succeed when the mail server is unreachable.
    Callers that need to react to a failure can check the return value.
    """
    html_content = render_to_string(template_name, context)

    message = EmailMultiAlternatives(subject, html_content, settings.DEFAULT_FROM_EMAIL, recipients)
    message.attach_alternative(html_content, "text/html")
    if reply_to:
        message.reply_to = reply_to

    try:
        # Not fail_silently: swallowing here would log success unconditionally.
        # smtplib.SMTPException and every socket error are OSError subclasses.
        message.send(fail_silently=False)
    except OSError:
        logger.exception("Could not send email %r to %s", subject, ", ".join(recipients))
        return False

    logger.info("Sent email %r to %s", subject, ", ".join(recipients))
    return True

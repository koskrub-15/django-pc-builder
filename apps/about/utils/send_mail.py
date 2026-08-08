import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_contact_message(name: str, email: str, message: str) -> None:
    subject = f"Contact form message from {name}"
    context = {"subject": subject, "name": name, "email": email, "message": message}
    html_content = render_to_string("email/contact_message.html", context)

    msg = EmailMultiAlternatives(subject, html_content, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
    msg.attach_alternative(html_content, "text/html")
    # The visitor typed this address; replying should go to them, not to the site.
    msg.reply_to = [email]
    msg.send(fail_silently=True)

    logger.info("Contact form message sent: %s", subject)

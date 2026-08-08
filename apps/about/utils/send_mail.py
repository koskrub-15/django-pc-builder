"""Delivery of the About page contact form."""

from django.conf import settings

from apps.base.utils.send_html_email import send_html_email


def send_contact_message(name: str, email: str, message: str) -> None:
    """Forward a contact form submission to the site owner."""
    subject = f"Contact form message from {name}"
    send_html_email(
        subject=subject,
        template_name="email/contact_message.html",
        context={"subject": subject, "name": name, "email": email, "message": message},
        recipients=[settings.DEFAULT_FROM_EMAIL],
        # The visitor typed this address; replying should go to them, not to the site.
        reply_to=[email],
    )

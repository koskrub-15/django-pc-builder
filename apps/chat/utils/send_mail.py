import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.builder.models.pc_build import PCBuildOrder

logger = logging.getLogger(__name__)


def notify_admin_about_message(user_email: str, username: str, user_message: str) -> None:
    subject = f"New message from {username}"
    html_content = render_to_string(
        "email/admin_message.html",
        {"username": username, "user_message": user_message, "user_email": user_email, "subject": subject},
    )
    msg = EmailMultiAlternatives(subject, html_content, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)
    logger.info("Email sent to admin: %s", subject)


def notify_user_about_order(user_email: str, username: str, order: PCBuildOrder, *, is_delivered: bool) -> None:
    if is_delivered:
        subject = "Your build has been delivered"
        message = "Your build has been delivered to you"
    else:
        subject = "Your build has been sent"
        message = "Your build is completed and has been sent to you"
    html_content = render_to_string(
        "email/order_message.html",
        {"username": username, "order": order, "subject": subject, "message": message},
    )
    msg = EmailMultiAlternatives(subject, html_content, settings.DEFAULT_FROM_EMAIL, [user_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)


def create_order(user_email: str, username: str, order: PCBuildOrder) -> None:
    subject = "New PC Build Order"
    context = {
        "username": username,
        "order": order,
        "subject": subject,
        "message": (
            "We've created a PC build order for you. "
            "We'll keep you updated on your order status via chat and email."
        ),
    }
    html_content = render_to_string("email/order_message.html", context)
    msg = EmailMultiAlternatives(subject, html_content, settings.DEFAULT_FROM_EMAIL, [user_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)

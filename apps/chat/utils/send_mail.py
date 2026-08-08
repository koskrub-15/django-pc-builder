"""Order and chat notifications sent to the customer and to the site owner."""

from django.conf import settings

from apps.base.utils.send_html_email import send_html_email
from apps.builder.models.pc_build import PCBuildOrder


def notify_admin_about_message(user_email: str, username: str, user_message: str) -> None:
    """Tell the site owner that a customer opened or resumed a conversation."""
    subject = f"New message from {username}"
    send_html_email(
        subject=subject,
        template_name="email/admin_message.html",
        context={
            "username": username,
            "user_message": user_message,
            "user_email": user_email,
            "subject": subject,
        },
        recipients=[settings.DEFAULT_FROM_EMAIL],
    )


def notify_user_about_order(user_email: str, username: str, order: PCBuildOrder, *, is_delivered: bool) -> None:
    """Tell the customer their build has been completed or delivered."""
    if is_delivered:
        subject = "Your build has been delivered"
        message = "Your build has been delivered to you"
    else:
        subject = "Your build has been sent"
        message = "Your build is completed and has been sent to you"

    send_html_email(
        subject=subject,
        template_name="email/order_message.html",
        context={"username": username, "order": order, "subject": subject, "message": message},
        recipients=[user_email],
    )


def create_order(user_email: str, username: str, order: PCBuildOrder) -> None:
    """Confirm to the customer that an order has been created for them."""
    subject = "New PC Build Order"
    send_html_email(
        subject=subject,
        template_name="email/order_message.html",
        context={
            "username": username,
            "order": order,
            "subject": subject,
            "message": (
                "We've created a PC build order for you. "
                "We'll keep you updated on your order status via chat and email."
            ),
        },
        recipients=[user_email],
    )

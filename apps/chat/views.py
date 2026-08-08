"""Chat screens: the room itself, and the staff actions that post into it."""

from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.views.decorators.http import require_POST

from apps.base.utils.is_admin import is_admin
from apps.builder.models.pc_build import OrderProgress, PCBuild, PCBuildOrder

from .models import ChatMessage, ChatThread
from .utils.access import get_accessible_thread
from .utils.send_mail import create_order, notify_admin_about_message


def _find_build(build_id: str | None) -> PCBuild | None:
    """Return the requested build, or None if the id is missing or unknown."""
    if not build_id or not build_id.isdigit():
        return None
    return PCBuild.objects.filter(id=int(build_id)).first()


def _parse_amount(raw: str | None) -> Decimal:
    """Parse a money amount from form input, falling back to zero."""
    try:
        return Decimal((raw or "0").strip())
    except InvalidOperation:
        return Decimal("0.00")


@login_required
def chat_room(request: HttpRequest, thread_id: int) -> HttpResponse:
    """Render one conversation, plus the order forms when staff open it."""
    thread = get_accessible_thread(request.user, thread_id)
    chat_messages = ChatMessage.objects.filter(thread=thread).select_related("sender").order_by("timestamp")

    context: dict[str, Any] = {
        "thread": thread,
        "chat_messages": chat_messages,
    }

    if request.user.is_staff:
        # total_price sums the components, so the picker needs them prefetched.
        context["builds"] = PCBuild.objects.prefetch_related("components")

    return render(request, "chat/chat_room.html", context)


@login_required
def send_message(request: HttpRequest, thread_id: int) -> HttpResponse:
    """Save a message and broadcast it to everyone watching the thread.

    The owner's first message, and any message after an hour of silence,
    also emails the site owner so a conversation is not missed.
    """
    if request.method == "POST":
        thread = get_accessible_thread(request.user, thread_id)
        message_text = request.POST.get("message", "").strip()

        if message_text:
            last_message = ChatMessage.objects.filter(thread=thread, sender=request.user).order_by("-timestamp").first()

            notify_admin = not last_message or (timezone.now() - last_message.timestamp > timedelta(hours=1))
            ChatMessage.objects.create(thread=thread, sender=request.user, text=message_text)

            async_to_sync(get_channel_layer().group_send)(
                f"chat_{thread_id}",
                {
                    "type": "chat_message",
                    "message": message_text,
                    "sender": request.user.username,
                    "is_html": False,
                },
            )

            if notify_admin and not request.user.is_staff:
                notify_admin_about_message(
                    user_email=request.user.email,
                    username=request.user.username,
                    user_message=message_text,
                )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return HttpResponse(status=204)
    return redirect("chat:chat_room", thread_id=thread_id)


@login_required
def get_messages(request: HttpRequest, thread_id: int) -> JsonResponse:
    """Return a thread as JSON, optionally only what is newer than last_id."""
    thread = get_accessible_thread(request.user, thread_id)

    last_id = request.GET.get("last_id", 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    messages_query = ChatMessage.objects.filter(thread=thread).select_related("sender").order_by("timestamp")
    if last_id > 0 and request.GET.get("only_new", "") == "true":
        messages_query = messages_query.filter(id__gt=last_id)

    messages_list = [
        {
            "id": msg.id,
            "text": msg.text,
            "sender": msg.sender.username,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in messages_query
    ]

    return JsonResponse({"messages": messages_list})


@login_required
@require_POST
@transaction.atomic
def create_order_from_chat(request: HttpRequest, thread_id: int) -> HttpResponse:
    """Create an order for the thread's customer and confirm it in the chat."""
    thread = get_accessible_thread(request.user, thread_id)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create orders")
        return redirect("chat:chat_room", thread_id=thread.id)

    build = _find_build(request.POST.get("build_id"))
    if build is None:
        messages.error(request, "Selected PC build does not exist")
        return redirect("chat:chat_room", thread_id=thread.id)

    customer = thread.user
    address = request.POST.get("address", "").strip()

    order = PCBuildOrder.objects.create(
        build=build,
        customer=customer,
        address=address,
        markup=_parse_amount(request.POST.get("markup")),
    )

    OrderProgress.objects.create(order=order)
    create_order(user_email=customer.email, username=customer.username, order=order)

    rows = format_html_join(
        "",
        "<tr><td>{}</td><td>{}</td></tr>",
        ((idx, component.name) for idx, component in enumerate(build.components.all(), 1)),
    )
    components_html = format_html(
        '<table class="table table-bordered table-sm mb-0" style="background:white;">'
        "<thead><tr><th>#</th><th>Component</th></tr></thead><tbody>{}</tbody></table>",
        rows,
    )

    ChatMessage.objects.create(
        thread=thread,
        sender=request.user,
        is_html=True,
        text=format_html(
            "A new PC build order has been created for you: '<b>{}</b>'.<br>"
            "Order number: <b>{}</b><br>"
            "Order address: <b>{}</b><br>"
            "Total price: <b>{} €</b><br>"
            "We'll keep you updated on your order status via chat and email.<br>"
            "Components:<br><br>{}",
            build.name,
            order.id,
            order.address,
            f"{order.total_price:.2f}",
            components_html,
        ),
    )

    messages.success(request, f"Order #{order.id} successfully created for {customer.username}")
    return redirect("chat:chat_room", thread_id=thread.id)


@login_required
@require_POST
@transaction.atomic
def send_component_list(request: HttpRequest, thread_id: int) -> HttpResponse:
    """Post a build's component and price breakdown into the chat."""
    thread = get_accessible_thread(request.user, thread_id)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to send component lists")
        return redirect("chat:chat_room", thread_id=thread.id)

    build = _find_build(request.POST.get("build_id"))
    if build is None:
        messages.error(request, "Selected PC build does not exist")
        return redirect("chat:chat_room", thread_id=thread.id)

    service_fee = _parse_amount(request.POST.get("service_fee"))

    rows = format_html_join(
        "",
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>",
        ((idx, component.name, f"{component.price:.2f}") for idx, component in enumerate(build.components.all(), 1)),
    )
    components_html = format_html(
        '<table class="table table-bordered table-sm mb-0" style="background:white;">'
        "<thead><tr><th>#</th><th>Component</th><th>Price (€)</th></tr></thead><tbody>{}</tbody></table>",
        rows,
    )

    ChatMessage.objects.create(
        thread=thread,
        sender=request.user,
        is_html=True,
        text=format_html(
            "Here's the component list for '<b>{}</b>':<br><br>"
            "Build total price: <b>{} €</b><br>"
            "Service fee: <b>{} €</b><br>"
            "Components breakdown:<br><br>{}<br>",
            build.name,
            f"{build.total_price:.2f}",
            f"{service_fee:.2f}",
            components_html,
        ),
    )

    messages.success(request, f"Component list for '{build.name}' sent successfully")
    return redirect("chat:chat_room", thread_id=thread.id)


@login_required
@user_passes_test(is_admin)
def thread_list(request: HttpRequest) -> HttpResponse:
    """List every conversation for staff."""
    threads = ChatThread.objects.select_related("user")
    return render(request, "chat/thread_list.html", {"threads": threads})


@login_required
def contact_admin(request: HttpRequest) -> HttpResponse:
    """Open the caller's conversation, creating it on first contact."""
    thread, _ = ChatThread.objects.get_or_create(user=request.user)
    return redirect("chat:chat_room", thread_id=thread.id)

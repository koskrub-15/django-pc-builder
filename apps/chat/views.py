from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.base.utils.is_admin import is_admin
from apps.builder.models.pc_build import OrderProgress, PCBuild, PCBuildOrder

from .models import ChatMessage, ChatThread
from .utils.send_mail import create_order, notify_admin_about_message


@login_required
def chat_room(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(ChatThread, id=thread_id)
    chat_messages = ChatMessage.objects.filter(thread=thread).order_by("timestamp")

    context: dict[str, Any] = {
        "thread": thread,
        "chat_messages": chat_messages,
    }

    if request.user.is_staff:
        context["builds"] = PCBuild.objects.all()

    return render(request, "chat/chat_room.html", context)


@login_required
def send_message(request: HttpRequest, thread_id: int) -> HttpResponse:
    if request.method == "POST":
        thread = get_object_or_404(ChatThread, id=thread_id)
        message_text = request.POST.get("message", "").strip()

        if message_text:
            last_message = (
                ChatMessage.objects.filter(thread=thread, sender=request.user)
                .order_by("-timestamp")
                .first()
            )

            notify_admin = not last_message or (timezone.now() - last_message.timestamp > timedelta(hours=1))
            ChatMessage.objects.create(thread=thread, sender=request.user, text=message_text)

            async_to_sync(get_channel_layer().group_send)(
                f"chat_{thread_id}",
                {
                    "type": "chat_message",
                    "message": message_text,
                    "sender": request.user.username,
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
    thread = get_object_or_404(ChatThread, id=thread_id)

    if not request.user.is_staff and request.user != thread.user:
        return JsonResponse({"error": "Access denied"}, status=403)

    last_id = request.GET.get("last_id", 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    messages_query = ChatMessage.objects.filter(thread=thread).order_by("timestamp")
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
@transaction.atomic
def create_order_from_chat(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(ChatThread, id=thread_id)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create orders")
        return redirect("chat:chat_room", thread_id=thread.id)

    customer = thread.user
    build_id = request.POST.get("build_id")
    address = request.POST.get("address", "").strip()
    markup = request.POST.get("markup", "0").strip()

    try:
        build = get_object_or_404(PCBuild, id=build_id)

        try:
            markup_decimal = Decimal(markup)
        except (InvalidOperation, TypeError):
            markup_decimal = Decimal("0.00")

        order = PCBuildOrder.objects.create(
            build=build,
            customer=customer,
            address=address,
            markup=markup_decimal,
        )

        OrderProgress.objects.create(order=order)
        create_order(user_email=customer.email, username=customer.username, order=order)

        components_html = (
            '<table class="table table-bordered table-sm mb-0" style="background:white;">'
            "<thead><tr><th>#</th><th>Component</th></tr></thead><tbody>"
        )
        for idx, component in enumerate(build.components.all(), 1):
            components_html += f"<tr><td>{idx}</td><td>{component.name}</td></tr>"
        components_html += "</tbody></table>"

        ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            text=(
                f"A new PC build order has been created for you: '<b>{build.name}</b>'.<br>"
                f"Order number: <b>{order.id}</b><br>"
                f"Order address: <b>{order.address}</b><br>"
                f"Total price: <b>{order.total_price:.2f} €</b><br>"
                f"We'll keep you updated on your order status via chat and email.<br>"
                f"Components:<br><br>{components_html}"
            ),
        )

        messages.success(request, f"Order #{order.id} successfully created for {customer.username}")
    except PCBuild.DoesNotExist:
        messages.error(request, "Selected PC build does not exist")

    return redirect("chat:chat_room", thread_id=thread.id)


@login_required
@transaction.atomic
def send_component_list(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(ChatThread, id=thread_id)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to send component lists")
        return redirect("chat:chat_room", thread_id=thread.id)

    if request.method == "POST":
        build_id = request.POST.get("build_id")
        service_fee = request.POST.get("service_fee", "0").strip()

        try:
            build = get_object_or_404(PCBuild, id=build_id)

            try:
                service_fee_decimal = Decimal(service_fee)
            except (InvalidOperation, TypeError):
                service_fee_decimal = Decimal("0.00")

            components_html = (
                '<table class="table table-bordered table-sm mb-0" style="background:white;">'
                "<thead><tr><th>#</th><th>Component</th><th>Price (€)</th></tr></thead><tbody>"
            )
            for idx, component in enumerate(build.components.all(), 1):
                components_html += f"<tr><td>{idx}</td><td>{component.name}</td><td>{component.price:.2f}</td></tr>"
            components_html += "</tbody></table>"

            ChatMessage.objects.create(
                thread=thread,
                sender=request.user,
                text=(
                    f"Here's the component list for '<b>{build.name}</b>':<br><br>"
                    f"Build total price: <b>{build.total_price:.2f} €</b><br>"
                    f"Service fee: <b>{service_fee_decimal:.2f} €</b><br>"
                    f"Components breakdown:<br><br>{components_html}<br>"
                ),
            )

            messages.success(request, f"Component list for '{build.name}' sent successfully")

        except PCBuild.DoesNotExist:
            messages.error(request, "Selected PC build does not exist")

    return redirect("chat:chat_room", thread_id=thread.id)


@login_required
@user_passes_test(is_admin)
def thread_list(request: HttpRequest) -> HttpResponse:
    threads = ChatThread.objects.all()
    return render(request, "chat/thread_list.html", {"threads": threads})


@login_required
def contact_admin(request: HttpRequest) -> HttpResponse:
    thread, _ = ChatThread.objects.get_or_create(user=request.user)
    return redirect("chat:chat_room", thread_id=thread.id)

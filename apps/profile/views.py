from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.builder.models.pc_build import PCBuildOrder


@login_required
def index(request: HttpRequest) -> HttpResponse:
    user = User.objects.get(username=request.user)
    orders = PCBuildOrder.objects.filter(customer=user).order_by("-created_on")
    context = {
        "orders": orders,
        "user": user,
    }
    return render(
        request=request,
        template_name="account/index.html",
        context=context,
    )

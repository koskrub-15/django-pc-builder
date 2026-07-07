from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.builder.models.pc_build import PCBuildOrder


@login_required
def index(request: HttpRequest) -> HttpResponse:
    orders = PCBuildOrder.objects.filter(customer=request.user).order_by("-created_on")
    return render(
        request=request,
        template_name="account/index.html",
        context={"orders": orders, "user": request.user},
    )

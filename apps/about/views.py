from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.about.forms import ContactForm
from apps.about.utils.send_mail import send_contact_message


def index(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            send_contact_message(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                message=form.cleaned_data["message"],
            )
            messages.success(request, "Thanks! Your message has been sent.")
            return redirect("about:index")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()

    return render(
        request=request,
        template_name="about/index.html",
        context={"form": form, "owner": settings.SITE_OWNER},
    )

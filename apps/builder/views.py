"""Staff-only screens for the build catalogue and order tracking."""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.base.utils.is_admin import is_admin
from apps.builder.forms import PCBuildForm, PCComponentForm
from apps.builder.models.pc_build import PCBuild, PCBuildOrder, PCComponent
from apps.chat.utils.send_mail import notify_user_about_order


@login_required
@user_passes_test(is_admin)
def progress_tracker(request: HttpRequest) -> HttpResponse:
    """Show every order's milestones and save the checkboxes on POST.

    Ticking "completed" or "delivered" for the first time stamps the date
    and emails the customer; clearing it removes the stamp again.
    """
    orders = PCBuildOrder.objects.select_related("progress", "build", "customer").prefetch_related(
        "build__components",
    )

    if request.method == "POST":
        for order in orders:
            progress = order.progress

            progress.are_components_ordered = bool(request.POST.get(f"ordered_{order.id}"))
            progress.are_components_arrived = bool(request.POST.get(f"arrived_{order.id}"))
            progress.are_components_installed = bool(request.POST.get(f"installed_{order.id}"))
            progress.is_pc_build_tested = bool(request.POST.get(f"tested_{order.id}"))

            is_completed = bool(request.POST.get(f"completed_{order.id}"))
            if is_completed and not progress.is_completed:
                progress.completed_on = timezone.now()
                notify_user_about_order(
                    user_email=order.customer.email,
                    username=order.customer.username,
                    order=order,
                    is_delivered=False,
                )
            elif not is_completed:
                progress.completed_on = None
            progress.is_completed = is_completed

            is_delivered = bool(request.POST.get(f"delivered_{order.id}"))
            if is_delivered and not progress.is_delivered:
                progress.delivered_on = timezone.now()
                notify_user_about_order(
                    user_email=order.customer.email,
                    username=order.customer.username,
                    order=order,
                    is_delivered=True,
                )
            elif not is_delivered:
                progress.delivered_on = None
            progress.is_delivered = is_delivered

            progress.save()
        return redirect("builder:tracker")
    return render(request, "builder/tracker.html", {"orders": orders})


@login_required
@user_passes_test(is_admin)
def list_of_pc_builds(request: HttpRequest) -> HttpResponse:
    """List the builds and create one from the form on the same page."""
    if request.method == "POST":
        form = PCBuildForm(request.POST)
        if form.is_valid():
            build = form.save()
            component_ids = [cid for cid in request.POST.getlist("components") if cid]
            build.components.set(PCComponent.objects.filter(id__in=component_ids))
            return redirect("builder:builds")
    else:
        form = PCBuildForm()

    builds = PCBuild.objects.prefetch_related("components")
    components = PCComponent.objects.all()
    return render(
        request,
        "builder/builds.html",
        {"form": form, "builds": builds, "all_components": components},
    )


@login_required
@user_passes_test(is_admin)
def update_build(request: HttpRequest, pk: int) -> HttpResponse:
    """Rename a build and replace its component set."""
    build = get_object_or_404(PCBuild, pk=pk)
    if request.method == "POST":
        form = PCBuildForm(request.POST, instance=build)
        if form.is_valid():
            build = form.save()
            component_ids = [cid for cid in request.POST.getlist("components") if cid]
            build.components.set(PCComponent.objects.filter(id__in=component_ids))
            return redirect("builder:builds")
    else:
        form = PCBuildForm(instance=build)

    components = PCComponent.objects.all()
    return render(
        request,
        "builder/builds.html",
        {"form": form, "build": build, "all_components": components},
    )


@login_required
@user_passes_test(is_admin)
def create_component(request: HttpRequest) -> HttpResponse:
    """Add a component to the catalogue."""
    if request.method == "POST":
        form = PCComponentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("builder:create_component")
    else:
        form = PCComponentForm()

    return render(request, "builder/component_actions.html", {"form": form})


@login_required
@user_passes_test(is_admin)
def edit_component(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a component; the change applies to every build using it."""
    component = get_object_or_404(PCComponent, pk=pk)
    if request.method == "POST":
        form = PCComponentForm(request.POST, instance=component)
        if form.is_valid():
            form.save()
            return redirect("builder:builds")
    else:
        form = PCComponentForm(instance=component)

    return render(request, "builder/component_actions.html", {"form": form, "component": component})

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.base.utils.is_admin import is_admin
from apps.blog.forms import CategoryForm, CommentForm, PostForm
from apps.blog.models.posts import Category, Comment, Post


def _post_list() -> QuerySet[Post]:
    """Return posts with everything the card template renders, in one round trip."""
    return Post.objects.prefetch_related("categories").annotate(comment_count=Count("comments", distinct=True))


def index(request: HttpRequest) -> HttpResponse:
    posts = _post_list().order_by("-created_on")
    paginator = Paginator(posts, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(
        request=request,
        template_name="blog/index.html",
        context=context,
    )


def blog_category(request: HttpRequest, category: str) -> HttpResponse:
    # The links that reach this view are built from Category.name, so the match
    # is exact: __contains also pulled in every category the name is a substring
    # of, and listed a post once per matching category.
    posts = _post_list().filter(categories__name__iexact=category).order_by("-created_on").distinct()
    paginator = Paginator(posts, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "category": category,
        "page_obj": page_obj,
    }
    return render(request=request, template_name="blog/category.html", context=context)


def blog_detail(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post.objects.prefetch_related("categories"), pk=pk)
    form = CommentForm()
    all_categories = Category.objects.all()

    if request.method == "POST":
        if "body" in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                if request.user.is_authenticated:
                    author = request.user.username
                else:
                    author = form.cleaned_data["author"] or "Anonymous"

                comment = Comment(
                    author=author,
                    body=form.cleaned_data["body"],
                    post=post,
                )
                comment.save()
                messages.success(request, "Your comment has been added!")
                return HttpResponseRedirect(request.path_info)
            messages.error(request, "Please correct the errors below.")
        else:
            form = CommentForm()

    comments = post.comments.all()
    context = {
        "post": post,
        "comments": comments,
        "form": form,
        "all_categories": all_categories,
        "user_authenticated": request.user.is_authenticated,
    }
    return render(request, "blog/detail.html", context)


@login_required
@user_passes_test(is_admin)
def create_post(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/blog")
    else:
        form = PostForm()
    return render(request, "blog/post_actions.html", {"form": form, "post": None})


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_post(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    messages.success(request, "Post deleted successfully!")
    return HttpResponseRedirect("/blog/")


@login_required
@user_passes_test(is_admin)
def update_post(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/blog")
    else:
        form = PostForm(instance=post)
    return render(request, "blog/post_actions.html", {"form": form, "post": post})


@login_required
@user_passes_test(is_admin)
def create_category(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully!")
            return HttpResponseRedirect(request.path_info)
    else:
        form = CategoryForm()

    categories = Category.objects.all().order_by("name")
    return render(
        request,
        "blog/category_actions.html",
        {
            "form": form,
            "categories": categories,
        },
    )


@login_required
@user_passes_test(is_admin)
def update_category(request: HttpRequest, pk: int) -> HttpResponse:
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully!")
            return HttpResponseRedirect("/blog/categories/")
    else:
        form = CategoryForm(instance=category)

    categories = Category.objects.all().order_by("name")
    return render(
        request,
        "blog/category_actions.html",
        {
            "form": form,
            "category": category,
            "categories": categories,
        },
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_category(request: HttpRequest, pk: int) -> HttpResponse:
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Category deleted successfully!")
    return HttpResponseRedirect("/blog/categories/")

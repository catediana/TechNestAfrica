from collections import OrderedDict

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

#from blog.models import Post
from Products.models import Product

# Template section order for product_list grouping (see ``_product_row_group``).
GROUP_ORDER = ["eggs", "broiler_chicken", "layer_chicken", "manure", "feed"]

GROUP_TITLES = {
    "eggs": "Eggs",
    "broiler_chicken": "Broiler chicken",
    "layer_chicken": "Layer chicken",
    "manure": "Manure",
    "feed": "Feed",
}


def _product_row_group(product_type: str) -> str:
    """Map ``Product.product_type`` value → key in ``GROUP_ORDER``."""
    if product_type.startswith("eggs_"):
        return "eggs"
    if product_type.startswith("manure_"):
        return "manure"
    if product_type.startswith("feed_"):
        return "feed"
    return product_type


def home(request):
    featured = Product.objects.filter(available=True, stock__gt=0)[:6]
   # recent_posts = Post.objects.filter(published=True)[:3]
    return render(
        request,
        "products/home.html",
        {
            "featured_products": featured,
            "recent_posts": recent_posts,
        },
    )


def product_list(request):
    qs = Product.objects.filter(available=True, stock__gt=0).order_by(
        "product_type", "name"
    )
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    group_filter = request.GET.get("group", "").strip()
    if group_filter in GROUP_ORDER:
        if group_filter == "eggs":
            qs = qs.filter(product_type__startswith="eggs_")
        elif group_filter == "manure":
            qs = qs.filter(product_type__startswith="manure_")
        elif group_filter == "feed":
            qs = qs.filter(product_type__startswith="feed_")
        else:
            qs = qs.filter(product_type=group_filter)

    buckets = OrderedDict((k, []) for k in GROUP_ORDER)
    for p in qs:
        buckets[_product_row_group(p.product_type)].append(p)

    sections = [
        (GROUP_TITLES[k], buckets[k])
        for k in GROUP_ORDER
        if buckets[k]
    ]
    return render(
        request,
        "products/product_list.html",
        {
            "sections": sections,
            "group_filter": group_filter,
            "search_query": q,
            "group_choices": [(k, GROUP_TITLES[k]) for k in GROUP_ORDER],
        },
    )


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related("extra_images"),
        pk=pk,
        available=True,
        stock__gt=0,
    )
    return render(request, "products/product_detail.html", {"product": product})

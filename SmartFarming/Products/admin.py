"""Product catalog admin — inline gallery rows sort via ``sort_order``."""

from django.contrib import admin

from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "product_type",
        "price",
        "stock",
        "available",
        "created_at",
    )
    list_filter = ("product_type", "available")
    search_fields = ("name", "description")
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "caption", "sort_order")
    list_filter = ("product",)

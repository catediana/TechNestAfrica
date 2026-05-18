"""Order admin — fulfilment ``status`` + rails ``payment_status`` / M-Pesa correlation IDs."""

from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "customer_name",
        "user",
        "quantity",
        "total_price",
        "status",
        "payment_status",
        "mpesa_receipt_number",
        "order_date",
    )
    list_filter = ("status", "payment_status", "order_date", "product")
    search_fields = (
        "customer_name",
        "email",
        "phone",
        "address",
        "mpesa_receipt_number",
        "mpesa_checkout_request_id",
    )
    readonly_fields = ("order_date",)
    date_hierarchy = "order_date"

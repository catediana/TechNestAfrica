"""
Persisted checkout rows — fulfilment ``status`` vs money ``payment_status``.

M-Pesa Daraja columns mirror STK Push / callback payloads (see ``Orders.views``).
"""

from django.conf import settings
from django.db import models

from Products.models import Product


class Order(models.Model):
    """
    Customer order line (one product per row — extend with OrderLine if you need carts).

    ``status`` — fulfilment lifecycle (admin updates when packing/shipping).
    ``payment_status`` — money rail (cash-on-delivery would stay UNPAID until staff confirms).
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        INITIATED = "initiated", "M-Pesa initiated"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    # Linked when checkout happens while authenticated; guest orders stay NULL.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField()
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    # Daraja STK identifiers — filled after stk_push / callback (join callback → row).
    mpesa_checkout_request_id = models.CharField(max_length=80, blank=True)
    mpesa_merchant_request_id = models.CharField(max_length=80, blank=True)
    mpesa_receipt_number = models.CharField(max_length=40, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"Order #{self.pk} — {self.product.name}"

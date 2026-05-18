"""
Order routing configuration for the checkout and payment workflow.

This module defines all URL endpoints used in the order lifecycle:
- Product checkout (order placement)
- Order confirmation and success page
- Real-time payment status checking
- M-Pesa STK push initiation
- M-Pesa callback webhook (server-to-server confirmation)
- Session cleanup after checkout completion

Together, these routes control the full customer journey from placing an order
to payment confirmation and final completion of the purchase process.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("place/", views.place_order, name="place_order"),
    path("success/", views.order_success, name="order_success"),
    path(
        "success/status/",
        views.order_payment_status,
        name="order_payment_status",
    ),
    path(
        "mpesa/<int:order_id>/",
        views.mpesa_initiate,
        name="mpesa_initiate",
    ),
    path("mpesa/callback/", views.mpesa_stk_callback, name="mpesa_stk_callback"),
    path("done/", views.clear_order_session, name="order_done"),
]

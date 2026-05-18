"""
Order processing and M-Pesa payment workflow (Daraja integration).

This module handles the full checkout lifecycle:

1. place_order:
   - Validates checkout form
   - Locks product stock using database transactions
   - Prevents overselling using row-level locking
   - Creates order and reduces inventory safely
   - Triggers customer notifications (non-blocking)

2. order_success:
   - Displays order confirmation page
   - Retrieves last order from session
   - Controls optional M-Pesa payment polling

3. order_payment_status:
   - Returns real-time payment status (JSON)
   - Secured using session-based order ownership

4. mpesa_initiate:
   - Initiates STK Push request via Daraja API
   - Normalizes phone numbers
   - Updates order with checkout identifiers
   - Sets payment state to INITIATED

5. mpesa_stk_callback:
   - Receives Safaricom payment callbacks (webhook)
   - Verifies payload and updates payment status
   - Handles duplicate callbacks safely
   - Ensures notifications are sent only once

6. clear_order_session:
   - Resets checkout session state after completion
"""

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from integrations.mpesa import mpesa_configured, stk_push
from integrations.mpesa_callback import parse_stk_callback_payload, stk_callback_ack_success
from integrations.notifications import notify_order_placed, notify_payment_confirmed

from .forms import PlaceOrderForm
from .models import Order
from Products.models import Product

logger = logging.getLogger(__name__)


def _normalize_mpesa_phone(raw: str) -> str:
    """Daraja expects MSISDN-style digits (Kenya: leading 254, no +)."""
    digits = "".join(c for c in raw if c.isdigit())
    if digits.startswith("254"):
        return digits
    if digits.startswith("0") and len(digits) >= 9:
        return "254" + digits[1:]
    if digits.startswith("7") and len(digits) == 9:
        return "254" + digits
    return digits


def place_order(request):
    # Optional deep-link from product detail: ?product=<pk>
    initial = {}
    pid = request.GET.get("product")
    if pid and str(pid).isdigit():
        if Product.objects.filter(
            pk=int(pid), available=True, stock__gt=0
        ).exists():
            initial["product"] = int(pid)

    if request.method == "POST":
        form = PlaceOrderForm(request.POST, user=request.user)
        if form.is_valid():
            # Lock product row so two tabs can’t oversell the same stock.
            with transaction.atomic():
                product = Product.objects.select_for_update().get(
                    pk=form.cleaned_data["product"].pk
                )
                qty = form.cleaned_data["quantity"]
                if qty > product.stock:
                    form.add_error(
                        "quantity",
                        f"Only {product.stock} units are available.",
                    )
                else:
                    order = form.save(commit=False)
                    order.total_price = product.price * qty
                    if request.user.is_authenticated:
                        order.user = request.user
                    order.save()
                    product.stock -= qty
                    if product.stock == 0:
                        product.available = False
                    product.save()
                    # Notifications must never roll back a committed order.
                    try:
                        notify_order_placed(order)
                    except Exception:
                        pass
                    request.session["last_order_id"] = order.pk
                    return redirect("order_success")
    else:
        form = PlaceOrderForm(initial=initial, user=request.user)

    return render(request, "orders/place_order.html", {"form": form})


def order_success(request):
    order_id = request.session.get("last_order_id")
    order = None
    mpesa_on = mpesa_configured()
    if order_id:
        order = Order.objects.filter(pk=order_id).select_related("product").first()
    poll_payment = False
    if order:
        terminal = order.payment_status in (
            Order.PaymentStatus.PAID,
            Order.PaymentStatus.FAILED,
        )
        if not terminal:
            # Poll only when STK might flip status (configured rail or push already sent).
            poll_payment = mpesa_on or order.payment_status == Order.PaymentStatus.INITIATED
    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
            "mpesa_available": mpesa_on,
            "poll_payment_status": poll_payment,
        },
    )


@require_http_methods(["GET"])
def order_payment_status(request):
    """
    JSON snapshot for the thank-you page — session must still own ``order_id``.

    Avoids exposing arbitrary orders: only ``last_order_id`` in this browser matches.
    """
    raw_id = request.GET.get("order_id", "")
    if not str(raw_id).isdigit():
        return JsonResponse({"error": "bad_request"}, status=400)
    oid = int(raw_id)
    if request.session.get("last_order_id") != oid:
        return JsonResponse({"error": "forbidden"}, status=403)
    order = Order.objects.filter(pk=oid).first()
    if order is None:
        return JsonResponse({"error": "not_found"}, status=404)
    terminal = order.payment_status in (
        Order.PaymentStatus.PAID,
        Order.PaymentStatus.FAILED,
    )
    return JsonResponse(
        {
            "payment_status": order.payment_status,
            "payment_label": order.get_payment_status_display(),
            "mpesa_receipt_number": order.mpesa_receipt_number or "",
            "terminal": terminal,
        }
    )


@require_http_methods(["POST"])
def mpesa_initiate(request, order_id):
    """Browser-initiated STK; session must still “own” this order id."""
    order = get_object_or_404(Order, pk=order_id)
    if request.session.get("last_order_id") != order.pk:
        return HttpResponseForbidden("Invalid session for this order.")
    phone_raw = (request.POST.get("mpesa_phone") or order.phone or "").strip()
    phone = _normalize_mpesa_phone(phone_raw)
    if len(phone) < 10:
        messages.error(request, "Enter a valid M-Pesa phone number.")
        return redirect("order_success")
    result = stk_push(
        phone_e164=phone,
        amount_kes=float(order.total_price),
        account_reference=f"ORD{order.pk}",
        transaction_desc=f"Order{order.pk}",
    )
    if result.get("ok") and result.get("checkout_request_id"):
        order.mpesa_checkout_request_id = result["checkout_request_id"] or ""
        mid = result.get("merchant_request_id") or ""
        order.mpesa_merchant_request_id = mid
        order.payment_status = Order.PaymentStatus.INITIATED
        order.save(update_fields=[
            "mpesa_checkout_request_id",
            "mpesa_merchant_request_id",
            "payment_status",
        ])
        messages.success(
            request,
            "STK Push sent. Check your phone to complete payment on M-Pesa.",
        )
    elif result.get("reason") == "mpesa_not_configured":
        messages.warning(
            request,
            "M-Pesa is not configured yet. Add Daraja credentials to your environment.",
        )
    else:
        messages.error(request, "Could not start M-Pesa payment. Try again later.")
    return redirect("order_success")


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_stk_callback(request):
    """
    Safaricom Daraja posts STK results here (configure MPESA_CALLBACK_URL).

    Optional shared secret: append ``?secret=<MPESA_CALLBACK_SECRET>`` to the
    Daraja CallBackURL so only callers who know the token can hit this endpoint.
    """
    cfg_secret = (getattr(settings, "MPESA_CALLBACK_SECRET", "") or "").strip()
    if cfg_secret and request.GET.get("secret") != cfg_secret:
        return HttpResponseForbidden("Invalid callback secret.")

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("M-Pesa callback: invalid JSON body")
        return JsonResponse(stk_callback_ack_success())

    parsed = parse_stk_callback_payload(payload)
    if not parsed or not parsed.get("checkout_request_id"):
        logger.warning("M-Pesa callback: unrecognized payload keys=%s", list(payload.keys()))
        # Still ACK — lets Daraja stop retrying malformed duplicates.
        return JsonResponse(stk_callback_ack_success())

    checkout_id = str(parsed["checkout_request_id"])
    rc = parsed.get("result_code")

    with transaction.atomic():
        order = (
            Order.objects.select_for_update()
            .filter(mpesa_checkout_request_id=checkout_id)
            .first()
        )
        if order is None:
            logger.warning(
                "M-Pesa callback: unknown CheckoutRequestID=%s", checkout_id
            )
            return JsonResponse(stk_callback_ack_success())

        mid = parsed.get("merchant_request_id")
        if (
            mid
            and order.mpesa_merchant_request_id
            and str(mid) != str(order.mpesa_merchant_request_id)
        ):
            # CheckoutRequestID is the primary join key; merchant id is a sanity check only.
            logger.warning(
                "M-Pesa merchant ID mismatch for order #%s (checkout still matched)",
                order.pk,
            )

        # Snapshot before mutating — used to send “payment confirmed” only once.
        previous_payment = order.payment_status

        if rc == 0:
            receipt = parsed.get("mpesa_receipt_number") or ""
            order.payment_status = Order.PaymentStatus.PAID
            order.mpesa_receipt_number = str(receipt)[:40]
            order.save(update_fields=["payment_status", "mpesa_receipt_number"])
            logger.info("M-Pesa paid order #%s receipt=%s", order.pk, receipt)
            if previous_payment != Order.PaymentStatus.PAID:
                try:
                    notify_payment_confirmed(order)
                except Exception:
                    logger.exception(
                        "Payment confirmation notify failed for order #%s", order.pk
                    )
        else:
            # Don’t overwrite PAID if a late failure ping arrives after success.
            if order.payment_status != Order.PaymentStatus.PAID:
                order.payment_status = Order.PaymentStatus.FAILED
                order.save(update_fields=["payment_status"])
            logger.info(
                "M-Pesa failed/cancelled order #%s code=%s desc=%s",
                order.pk,
                rc,
                parsed.get("result_desc"),
            )

    return JsonResponse(stk_callback_ack_success())


def clear_order_session(request):
    """Drop ``last_order_id`` after the shopper leaves the success funnel."""
    request.session.pop("last_order_id", None)
    return redirect("home")

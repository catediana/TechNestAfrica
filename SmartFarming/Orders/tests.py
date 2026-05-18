import json

from django.test import TestCase, override_settings
from django.urls import reverse

from integrations.mpesa_callback import parse_stk_callback_payload

from Orders.models import Order
from Products.models import Product


class OrderFlowTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Orderable broiler",
            product_type=Product.ProductType.BROILER_CHICKEN,
            price="600.00",
            stock=4,
            available=True,
        )

    def test_place_order_reduces_stock_and_redirects(self):
        url = reverse("place_order")
        payload = {
            "product": self.product.pk,
            "customer_name": "Jane Customer",
            "email": "jane@example.com",
            "phone": "+254700000000",
            "address": "Nairobi",
            "quantity": 2,
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)
        order = Order.objects.get()
        self.assertEqual(order.total_price, self.product.price * 2)
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_order_success_requires_session_order(self):
        session = self.client.session
        session["last_order_id"] = 999999
        session.save()
        response = self.client.get(reverse("order_success"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "#999999")


class OrderPaymentPollTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Poll SKU",
            product_type=Product.ProductType.BROILER_CHICKEN,
            price="50.00",
            stock=3,
            available=True,
        )

    def test_payment_poll_requires_session_order(self):
        order = Order.objects.create(
            product=self.product,
            customer_name="p",
            email="p@example.com",
            address="a",
            quantity=1,
            total_price="50.00",
            payment_status=Order.PaymentStatus.INITIATED,
        )
        url = reverse("order_payment_status") + f"?order_id={order.pk}"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

        session = self.client.session
        session["last_order_id"] = order.pk
        session.save()
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, 200)
        payload = json.loads(res2.content.decode())
        self.assertEqual(payload["payment_status"], Order.PaymentStatus.INITIATED)
        self.assertFalse(payload["terminal"])

    def test_payment_poll_marks_terminal_when_paid(self):
        order = Order.objects.create(
            product=self.product,
            customer_name="p",
            email="p@example.com",
            address="a",
            quantity=1,
            total_price="50.00",
            payment_status=Order.PaymentStatus.PAID,
            mpesa_receipt_number="Z99",
        )
        session = self.client.session
        session["last_order_id"] = order.pk
        session.save()
        res = self.client.get(
            reverse("order_payment_status") + f"?order_id={order.pk}"
        )
        self.assertEqual(res.status_code, 200)
        payload = json.loads(res.content.decode())
        self.assertTrue(payload["terminal"])
        self.assertEqual(payload["mpesa_receipt_number"], "Z99")


class MpesaCallbackTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Broiler",
            product_type=Product.ProductType.BROILER_CHICKEN,
            price="100.00",
            stock=2,
            available=True,
        )
        self.order = Order.objects.create(
            product=self.product,
            customer_name="x",
            email="x@example.com",
            address="addr",
            quantity=1,
            total_price="100.00",
            mpesa_checkout_request_id="ws_CO_TESTCHECKOUT",
            mpesa_merchant_request_id="mr_mid",
            payment_status=Order.PaymentStatus.INITIATED,
        )

    def test_parse_stk_payload_extracts_receipt(self):
        body = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "mr_mid",
                    "CheckoutRequestID": "ws_CO_TESTCHECKOUT",
                    "ResultCode": 0,
                    "ResultDesc": "ok",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 100},
                            {"Name": "MpesaReceiptNumber", "Value": "R123XYZ"},
                        ]
                    },
                }
            }
        }
        parsed = parse_stk_callback_payload(body)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["checkout_request_id"], "ws_CO_TESTCHECKOUT")
        self.assertEqual(parsed["result_code"], 0)
        self.assertEqual(parsed["mpesa_receipt_number"], "R123XYZ")

    def test_callback_marks_paid(self):
        url = reverse("mpesa_stk_callback")
        body = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "mr_mid",
                    "CheckoutRequestID": "ws_CO_TESTCHECKOUT",
                    "ResultCode": 0,
                    "ResultDesc": "ok",
                    "CallbackMetadata": {
                        "Item": [{"Name": "MpesaReceiptNumber", "Value": "ABC"}],
                    },
                }
            }
        }
        res = self.client.post(
            url,
            data=json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.mpesa_receipt_number, "ABC")

    def test_callback_respects_optional_secret(self):
        url = reverse("mpesa_stk_callback")
        body = {"Body": {"stkCallback": {"CheckoutRequestID": "x"}}}

        with override_settings(MPESA_CALLBACK_SECRET="s"):
            res = self.client.post(
                url,
                data=json.dumps(body),
                content_type="application/json",
            )
            self.assertEqual(res.status_code, 403)

            ok_url = f"{url}?secret=s"
            res2 = self.client.post(
                ok_url,
                data=json.dumps(body),
                content_type="application/json",
            )
            self.assertEqual(res2.status_code, 200)

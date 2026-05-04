from django.test import TestCase
from django.urls import reverse

from Products.models import Product


class ProductViewsTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Demo tray eggs",
            product_type=Product.ProductType.EGGS_TRAY,
            price="500.00",
            stock=5,
            description="Test product",
            available=True,
        )

    def test_home_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TechNest Africa")

    def test_product_list_contains_product(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_detail(self):
        url = reverse("product_detail", args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)


"""
Storefront SKUs + optional gallery rows (``ProductImage``) for detail-page carousels.
"""

from django.db import models


class Product(models.Model):
    """Poultry catalog aligned with TechNest Africa product categories."""

    class ProductType(models.TextChoices):
        EGGS_TRAY = "eggs_tray", "Eggs (tray)"
        EGGS_HALF_TRAY = "eggs_half_tray", "Eggs (half tray)"
        BROILER_CHICKEN = "broiler_chicken", "Broiler chicken"
        LAYER_CHICKEN = "layer_chicken", "Layer chicken"
        MANURE_BAGS = "manure_bags", "Manure (bags)"
        MANURE_BULK = "manure_bulk", "Manure (bulk)"
        FEED_STARTER = "feed_starter", "Feed (starter)"
        FEED_GROWER = "feed_grower", "Feed (grower)"
        FEED_FINISHER = "feed_finisher", "Feed (finisher)"

    name = models.CharField(max_length=120)

    #  Added default to prevent migration crash
    product_type = models.CharField(
        max_length=32,
        choices=ProductType.choices,
        default=ProductType.EGGS_TRAY
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    image = models.ImageField(upload_to="product_images/", blank=True)
    description = models.TextField(blank=True)

    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["product_type", "name"]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """
    Extra photos beyond ``Product.image`` (hero/main shot).
    Ordered by ``sort_order`` then PK.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="extra_images"
    )

    image = models.ImageField(upload_to="product_images/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]

    def __str__(self):
        return f"{self.product.name} — image {self.pk}"
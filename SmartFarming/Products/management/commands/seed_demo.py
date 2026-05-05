"""Populate catalog demo SKUs — no-op when ``Product`` rows already exist."""

from django.core.management.base import BaseCommand

from Products.models import Product

# Tuples: (display name, ProductType enum member, price string, stock int, description).
DEMO_PRODUCTS = [
    (
        "Farm eggs — full tray (30 eggs)",
        Product.ProductType.EGGS_TRAY,
        "520.00",
        120,
        "Grade A eggs from our layers; uniform size and strong shells.",
    ),
    (
        "Farm eggs — half tray",
        Product.ProductType.EGGS_HALF_TRAY,
        "280.00",
        80,
        "Half tray option for smaller households and cafés.",
    ),
    (
        "Broiler chicken — dressed",
        Product.ProductType.BROILER_CHICKEN,
        "650.00",
        45,
        "Fresh dressed broilers; ideal weight for retail and catering.",
    ),
    (
        "Layer chicken — mature",
        Product.ProductType.LAYER_CHICKEN,
        "520.00",
        30,
        "Spent or mature layers suited for stew and soup.",
    ),
    (
        "Organic manure — 50 kg bag",
        Product.ProductType.MANURE_BAGS,
        "350.00",
        60,
        "Composted poultry manure for gardens and greenhouse crops.",
    ),
    (
        "Bulk manure — per tonne",
        Product.ProductType.MANURE_BULK,
        "4500.00",
        12,
        "Loose bulk manure for larger farms; delivery coordinated offline.",
    ),
    (
        "Starter mash — 70 kg",
        Product.ProductType.FEED_STARTER,
        "3850.00",
        40,
        "High-protein starter for chicks up to 3 weeks.",
    ),
    (
        "Grower pellets — 70 kg",
        Product.ProductType.FEED_GROWER,
        "3600.00",
        55,
        "Balanced grower ration for pullets and slow-grow broilers.",
    ),
    (
        "Finisher pellets — 70 kg",
        Product.ProductType.FEED_FINISHER,
        "3550.00",
        48,
        "Energy-dense finisher for market-ready broilers.",
    ),
]


class Command(BaseCommand):
    """Idempotent catalog filler — align tuples with ``Product`` fields + ``ProductType``."""

    help = "Load demo poultry catalog entries (skips if products already exist)."

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING("Products already exist — skipping seed."))
            return
        rows = [
            Product(
                name=name,
                product_type=pt,
                price=price,
                stock=stock,
                description=desc,
                available=True,
            )
            for name, pt, price, stock, desc in DEMO_PRODUCTS
        ]
        Product.objects.bulk_create(rows)
        self.stdout.write(self.style.SUCCESS(f"Created {len(rows)} demo products."))

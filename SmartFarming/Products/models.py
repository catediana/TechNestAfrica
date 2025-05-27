from django.db import models


#product model to display the product available
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Eggs', 'Eggs'),
        ('Chicks', 'Chicks'),
        ('Chicken', 'Chicken'),
    ]

    SUBCATEGORY_CHOICES = [
        ('Broilers', 'Broilers'),
        ('Layers', 'Layers'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=50, choices=SUBCATEGORY_CHOICES, blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/', blank=True)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


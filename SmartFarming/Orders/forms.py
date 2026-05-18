"""
Customer checkout form for placing poultry product orders.

This form:
- Lets customers choose available products
- Collects customer contact and delivery details
- Prefills user information when logged in
- Prevents ordering more items than available stock
- Applies styled input fields for frontend templates

Stock validation happens here for user-friendly feedback,
and again in the view for database safety during checkout.
"""

from django import forms

from Products.models import Product

from .models import Order


class PlaceOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["product", "customer_name", "email", "phone", "address", "quantity"]
        widgets = {
            "product": forms.Select(attrs={"class": "input"}),
            "customer_name": forms.TextInput(
                attrs={"class": "input", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "input", "autocomplete": "email"}
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "input",
                    "autocomplete": "tel",
                    "placeholder": "+254 …",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "input textarea",
                    "rows": 3,
                    "autocomplete": "street-address",
                }
            ),
            "quantity": forms.NumberInput(attrs={"class": "input", "min": 1}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # Dropdown only shows lines that can actually be purchased right now.
        self.fields["product"].queryset = Product.objects.filter(
            available=True, stock__gt=0
        ).order_by("product_type", "name")
        self.fields["product"].empty_label = "Choose a product…"
        if user and user.is_authenticated:
            fn = (user.get_full_name() or "").strip()
            self.fields["customer_name"].initial = fn or user.username
            self.fields["email"].initial = user.email or ""
            profile = getattr(user, "profile", None)
            if profile is not None:
                self.fields["phone"].initial = profile.phone or ""

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        qty = cleaned.get("quantity")
        if product is not None and qty is not None and qty > product.stock:
            self.add_error(
                "quantity",
                f"Only {product.stock} units are available for this product.",
            )
        return cleaned

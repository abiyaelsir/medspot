from django.db import models
from django.conf import settings
from pharmacies.models import Pharmacy
from medicines.models import Medicine

class Alert(models.Model):
    ALERT_TYPE_CHOICES = [
        ("low_stock", "Low Stock"),
        ("expiration", "Expiration"),
        ("other", "Other"),
    ]
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name="alerts")
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    message = models.TextField(blank=True)
    acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.pharmacy}"
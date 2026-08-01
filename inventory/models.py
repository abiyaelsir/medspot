from django.db import models
from pharmacies.models import Pharmacy
from medicines.models import Medicine

class Inventory(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name="inventories")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="inventories")
    quantity = models.IntegerField(default=0)
    minimum_threshold = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("pharmacy", "medicine")

    def __str__(self):
        return f"{self.medicine} @ {self.pharmacy}: {self.quantity}"
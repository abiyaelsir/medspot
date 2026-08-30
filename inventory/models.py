from django.db import models
from django.conf import settings
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


class InventoryUpdateLog(models.Model):
    """
    Immutable audit log for all inventory modifications.
    Records every CREATE, UPDATE, DELETE, and BULK_UPLOAD operation.
    """
    OPERATION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('BULK_UPLOAD', 'Bulk Upload'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inventory_logs")
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.PROTECT, related_name="inventory_logs")
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, null=True, blank=True, related_name="inventory_logs")
    
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    
    # Store the change details as JSON-like text
    # For UPDATE: stores old and new values
    # For CREATE/DELETE: stores the full record
    # For BULK_UPLOAD: stores summary
    old_quantity = models.IntegerField(null=True, blank=True)
    new_quantity = models.IntegerField(null=True, blank=True)
    old_threshold = models.IntegerField(null=True, blank=True)
    new_threshold = models.IntegerField(null=True, blank=True)
    
    # Additional details field for bulk upload info or other notes
    details = models.TextField(blank=True, default="")
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['pharmacy', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_operation_display()} - {self.medicine} @ {self.pharmacy} - {self.timestamp}"

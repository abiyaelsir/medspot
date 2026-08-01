from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("pharmacy", "alert_type", "medicine", "created_at", "acknowledged")
    search_fields = ("pharmacy__name", "message")
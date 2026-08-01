from django.contrib import admin
from .models import Medicine

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "active_ingredient", "category", "dosage_form")
    search_fields = ("name", "active_ingredient", "category")
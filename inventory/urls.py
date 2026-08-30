# inventory/urls.py
from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("dashboard/", views.pharmacist_dashboard, name="dashboard"),
    path("medicine/add/", views.add_medicine, name="add_medicine"),
    path("medicine/<int:inventory_id>/edit/", views.edit_medicine, name="edit_medicine"),
    path("medicine/<int:inventory_id>/delete/", views.delete_medicine, name="delete_medicine"),
    path("upload/", views.upload_inventory, name="upload_inventory"),
    path("audit-log/", views.audit_log, name="audit_log"),
]

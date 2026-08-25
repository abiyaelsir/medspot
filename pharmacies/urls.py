# pharmacies/urls.py
from django.urls import path
from . import views

app_name = "pharmacies"

urlpatterns = [
    path("dashboard/", views.pharmacist_dashboard, name="dashboard"),
]
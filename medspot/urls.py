#name=medspot/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("users.urls", namespace="users")),
    path("pharmacies/", include("pharmacies.urls", namespace="pharmacies")),
]
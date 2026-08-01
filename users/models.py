from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("pharmacist", "Pharmacist"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="patient")

    def __str__(self):
        return f"{self.username} ({self.role})"
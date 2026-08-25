# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from pharmacies.models import Pharmacy

class PatientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.role = "patient"
        user.is_active = True
        user.is_verified = True
        if commit:
            user.save()
        return user

class PharmacistRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    pharmacy_name = forms.CharField(required=True)
    pharmacy_address = forms.CharField(widget=forms.Textarea, required=True)
    latitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    longitude = forms.DecimalField(required=False, max_digits=9, decimal_places=6)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",
                  "pharmacy_name", "pharmacy_address", "latitude", "longitude")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.role = "pharmacist"
        user.is_active = False   # block login until admin approves
        user.is_verified = False
        if commit:
            user.save()
            Pharmacy.objects.create(
                name=self.cleaned_data["pharmacy_name"],
                address=self.cleaned_data["pharmacy_address"],
                latitude=self.cleaned_data.get("latitude") or None,
                longitude=self.cleaned_data.get("longitude") or None,
                owner=user,
            )
        return user
from django import forms
from django.core.exceptions import ValidationError
from .models import Inventory
from medicines.models import Medicine


class MedicineInventoryForm(forms.ModelForm):
    """
    Form for adding/editing medicines in a pharmacy's inventory.
    """
    medicine_name = forms.CharField(
        max_length=255,
        label="Medicine Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Panadol'
        })
    )
    active_ingredient = forms.CharField(
        max_length=255,
        label="Active Ingredient",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Paracetamol'
        })
    )
    category = forms.CharField(
        max_length=255,
        label="Category",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Analgesic'
        })
    )
    strength = forms.CharField(
        max_length=100,
        label="Strength",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 500 mg'
        })
    )

    class Meta:
        model = Inventory
        fields = ['quantity', 'minimum_threshold']
        labels = {
            'quantity': 'Quantity',
            'minimum_threshold': 'Minimum Safety Threshold',
        }
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
            'minimum_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        return quantity

    def clean_minimum_threshold(self):
        threshold = self.cleaned_data.get('minimum_threshold')
        if threshold is not None and threshold < 0:
            raise ValidationError("Minimum threshold cannot be negative.")
        return threshold

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        threshold = cleaned_data.get('minimum_threshold')

        if quantity is not None and threshold is not None and quantity < threshold:
            # This is a warning, not a hard error - allow it but could warn user
            pass

        return cleaned_data

    def save(self, commit=True, pharmacy=None, is_update=False):
        """
        Override save to handle medicine creation/lookup and return the inventory object.
        
        Args:
            commit: Whether to save to database
            pharmacy: The pharmacy to associate this inventory with
            is_update: Whether this is an update (vs create)
        
        Returns:
            The Inventory instance
        """
        inventory = super().save(commit=False)

        if pharmacy:
            inventory.pharmacy = pharmacy

        # Get or create the Medicine based on form fields
        medicine_name = self.cleaned_data.get('medicine_name')
        active_ingredient = self.cleaned_data.get('active_ingredient', '')
        category = self.cleaned_data.get('category', '')
        strength = self.cleaned_data.get('strength', '')

        if medicine_name:
            # For now, create/get medicine by name
            # In a production system, you might want to check for duplicates more carefully
            medicine, created = Medicine.objects.get_or_create(
                name=medicine_name,
                defaults={
                    'active_ingredient': active_ingredient,
                    'category': category,
                    'dosage_form': strength,
                }
            )
            inventory.medicine = medicine

        if commit:
            inventory.save()

        return inventory


class InventoryUploadForm(forms.Form):
    """
    Form for uploading CSV or Excel files containing inventory data.
    """
    file = forms.FileField(
        label="Upload CSV or Excel (.xlsx) file",
        help_text="Supported formats: CSV, Excel (.xlsx)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx'
        })
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx')):
                raise ValidationError("File must be CSV or Excel (.xlsx) format.")
            
            # Check file size (limit to 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be under 5MB.")
        
        return file


class QuickUpdateQuantityForm(forms.Form):
    """
    Simple form for quickly updating the quantity of an existing inventory item.
    """
    quantity = forms.IntegerField(
        label="Quantity",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )
    minimum_threshold = forms.IntegerField(
        label="Minimum Safety Threshold",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        return quantity

    def clean_minimum_threshold(self):
        threshold = self.cleaned_data.get('minimum_threshold')
        if threshold is not None and threshold < 0:
            raise ValidationError("Minimum threshold cannot be negative.")
        return threshold

# inventory/forms.py
from django import forms
from medicines.models import Medicine
from .models import Inventory


class MedicineInventoryForm(forms.Form):
    """
    Form for adding or editing medicines in pharmacy inventory.
    Allows selection of existing medicine or creation of new one.
    """
    medicine_name = forms.CharField(
        max_length=255,
        required=True,
        label="Medicine Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter medicine name',
            'autocomplete': 'off'
        })
    )
    
    active_ingredient = forms.CharField(
        max_length=255,
        required=False,
        label="Active Ingredient",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Paracetamol'
        })
    )
    
    category = forms.CharField(
        max_length=255,
        required=False,
        label="Category",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Analgesic, Antibiotic'
        })
    )
    
    strength = forms.CharField(
        max_length=100,
        required=False,
        label="Strength/Dosage Form",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 500mg, tablet, syrup'
        })
    )
    
    quantity = forms.IntegerField(
        required=True,
        label="Quantity",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )
    
    minimum_threshold = forms.IntegerField(
        required=True,
        label="Minimum Threshold",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'help_text': 'Alert when quantity falls below this'
        })
    )
    
    def save(self, pharmacy, is_update=False):
        """
        Save the medicine and create/update inventory record.
        
        Args:
            pharmacy: The Pharmacy instance
            is_update: Whether this is updating an existing inventory
        
        Returns:
            Inventory instance
        """
        medicine_name = self.cleaned_data['medicine_name'].strip()
        active_ingredient = self.cleaned_data.get('active_ingredient', '').strip()
        category = self.cleaned_data.get('category', '').strip()
        strength = self.cleaned_data.get('strength', '').strip()
        quantity = self.cleaned_data['quantity']
        minimum_threshold = self.cleaned_data['minimum_threshold']
        
        # Get or create medicine
        medicine, created = Medicine.objects.get_or_create(
            name=medicine_name,
            defaults={
                'active_ingredient': active_ingredient,
                'category': category,
                'dosage_form': strength,
            }
        )
        
        # Update medicine details if provided and not just updating quantity
        if not is_update or active_ingredient:
            medicine.active_ingredient = active_ingredient or medicine.active_ingredient
            medicine.category = category or medicine.category
            medicine.dosage_form = strength or medicine.dosage_form
            medicine.save()
        
        # Create or update inventory
        if is_update:
            # Assume inventory is already fetched and we're just updating quantities
            # This is handled by the view
            pass
        else:
            inventory, _ = Inventory.objects.get_or_create(
                pharmacy=pharmacy,
                medicine=medicine,
                defaults={
                    'quantity': quantity,
                    'minimum_threshold': minimum_threshold,
                }
            )
        
        # Return the medicine for inventory update
        return Inventory.objects.get(pharmacy=pharmacy, medicine=medicine)


class InventoryUploadForm(forms.Form):
    """
    Form for bulk uploading inventory via CSV or Excel file.
    """
    file = forms.FileField(
        label="Upload File (CSV or Excel)",
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx'
        }),
        help_text="Supported formats: CSV (.csv) or Excel (.xlsx)"
    )
    
    def clean_file(self):
        """
        Validate file type and size.
        """
        file = self.cleaned_data['file']
        
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File size must not exceed 5MB.")
        
        # Check file extension
        allowed_extensions = ['csv', 'xlsx']
        file_name = file.name.lower()
        
        if not any(file_name.endswith(f'.{ext}') for ext in allowed_extensions):
            raise forms.ValidationError(
                f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        return file


class QuickUpdateQuantityForm(forms.Form):
    """
    Form for quick updates to medicine quantity (can be used in AJAX).
    """
    quantity = forms.IntegerField(
        required=True,
        min_value=0,
        label="Quantity",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )
    
    minimum_threshold = forms.IntegerField(
        required=False,
        min_value=0,
        label="Minimum Threshold",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )

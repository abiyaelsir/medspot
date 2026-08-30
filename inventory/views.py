# inventory/views.py
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from users.decorators import role_required
from pharmacies.models import Pharmacy
from medicines.models import Medicine
from .models import Inventory, InventoryUpdateLog
from .forms import MedicineInventoryForm, InventoryUploadForm, QuickUpdateQuantityForm

try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_pharmacist_pharmacy(user):
    """
    Get the pharmacy owned by the logged-in pharmacist.
    Returns None if the user is not a pharmacist or doesn't own a pharmacy.
    """
    if not hasattr(user, 'pharmacies') or not user.pharmacies.exists():
        return None
    return user.pharmacies.first()


def create_audit_log(user, pharmacy, medicine, operation, old_qty=None, new_qty=None, 
                     old_threshold=None, new_threshold=None, details=""):
    """
    Create an immutable audit log entry for an inventory operation.
    """
    InventoryUpdateLog.objects.create(
        user=user,
        pharmacy=pharmacy,
        medicine=medicine,
        operation=operation,
        old_quantity=old_qty,
        new_quantity=new_qty,
        old_threshold=old_threshold,
        new_threshold=new_threshold,
        details=details
    )


# ============================================================================
# PHARMACIST DASHBOARD
# ============================================================================

@login_required(login_url='users:login')
@role_required('pharmacist', require_verified=True)
def pharmacist_dashboard(request):
    """
    Main dashboard for verified pharmacists.
    Displays inventory summary and list of medicines.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        messages.error(request, "You do not have an associated pharmacy.")
        return redirect('users:login')
    
    # Get all inventory items for this pharmacy
    inventory_items = Inventory.objects.filter(pharmacy=pharmacy).select_related('medicine').order_by('medicine__name')
    
    # Calculate stats
    total_medicines = inventory_items.count()
    low_stock_count = sum(1 for item in inventory_items if item.quantity <= item.minimum_threshold and item.minimum_threshold > 0)
    
    context = {
        'pharmacy': pharmacy,
        'inventory_items': inventory_items,
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
    }
    
    return render(request, 'inventory/dashboard.html', context)


# ============================================================================
# ADD MEDICINE
# ============================================================================

@login_required(login_url='users:login')
@role_required('pharmacist', require_verified=True)
def add_medicine(request):
    """
    Add a new medicine to the pharmacy's inventory.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        messages.error(request, "You do not have an associated pharmacy.")
        return redirect('users:login')
    
    if request.method == 'POST':
        form = MedicineInventoryForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                inventory = form.save(pharmacy=pharmacy)
                
                # Create audit log
                create_audit_log(
                    user=user,
                    pharmacy=pharmacy,
                    medicine=inventory.medicine,
                    operation='CREATE',
                    new_qty=inventory.quantity,
                    new_threshold=inventory.minimum_threshold,
                    details=f"Initial stock: {inventory.quantity}, Threshold: {inventory.minimum_threshold}"
                )
            
            messages.success(request, f"Medicine '{inventory.medicine.name}' added successfully!")
            return redirect('inventory:dashboard')
    else:
        form = MedicineInventoryForm()
    
    context = {
        'form': form,
        'pharmacy': pharmacy,
        'action': 'Add Medicine',
    }
    
    return render(request, 'inventory/add_edit_medicine.html', context)


# ============================================================================
# EDIT MEDICINE
# ============================================================================

@login_required(login_url='users:login')
@role_required('pharmacist', require_verified=True)
def edit_medicine(request, inventory_id):
    """
    Edit an existing medicine in the pharmacy's inventory.
    Ensures the inventory belongs to the pharmacist's pharmacy.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        messages.error(request, "You do not have an associated pharmacy.")
        return redirect('users:login')
    
    # Verify ownership: inventory must belong to this pharmacy
    inventory = get_object_or_404(Inventory, id=inventory_id, pharmacy=pharmacy)
    
    if request.method == 'POST':
        form = MedicineInventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            with transaction.atomic():
                # Store old values for audit log
                old_qty = inventory.quantity
                old_threshold = inventory.minimum_threshold
                
                inventory = form.save(pharmacy=pharmacy, is_update=True)
                
                # Create audit log only if something changed
                if old_qty != inventory.quantity or old_threshold != inventory.minimum_threshold:
                    create_audit_log(
                        user=user,
                        pharmacy=pharmacy,
                        medicine=inventory.medicine,
                        operation='UPDATE',
                        old_qty=old_qty,
                        new_qty=inventory.quantity,
                        old_threshold=old_threshold,
                        new_threshold=inventory.minimum_threshold,
                        details=f"Qty: {old_qty} → {inventory.quantity}, Threshold: {old_threshold} → {inventory.minimum_threshold}"
                    )
            
            messages.success(request, f"Medicine '{inventory.medicine.name}' updated successfully!")
            return redirect('inventory:dashboard')
    else:
        form = MedicineInventoryForm(instance=inventory, initial={
            'medicine_name': inventory.medicine.name,
            'active_ingredient': inventory.medicine.active_ingredient,
            'category': inventory.medicine.category,
            'strength': inventory.medicine.dosage_form,
        })
    
    context = {
        'form': form,
        'pharmacy': pharmacy,
        'action': 'Edit Medicine',
        'inventory': inventory,
    }
    
    return render(request, 'inventory/add_edit_medicine.html', context)


# ============================================================================
# DELETE MEDICINE
# ============================================================================

@login_required(login_url='users:login')
@role_required('pharmacist', require_verified=True)
def delete_medicine(request, inventory_id):
    """
    Delete a medicine from the pharmacy's inventory.
    Shows a confirmation page for GET, handles deletion for POST.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        messages.error(request, "You do not have an associated pharmacy.")
        return redirect('users:login')
    
    # Verify ownership
    inventory = get_object_or_404(Inventory, id=inventory_id, pharmacy=pharmacy)
    
    if request.method == 'POST':
        medicine_name = inventory.medicine.name
        medicine = inventory.medicine
        
        with transaction.atomic():
            # Create audit log before deletion
            create_audit_log(
                user=user,
                pharmacy=pharmacy,
                medicine=medicine,
                operation='DELETE',
                old_qty=inventory.quantity,
                old_threshold=inventory.minimum_threshold,
                details=f"Deleted inventory: Qty was {inventory.quantity}, Threshold was {inventory.minimum_threshold}"
            )
            
            # Delete the inventory record
            inventory.delete()
        
        messages.success(request, f"Medicine '{medicine_name}' removed from inventory.")
        return redirect('inventory:dashboard')
    
    context = {
        'inventory': inventory,
        'pharmacy': pharmacy,
    }
    
    return render(request, 'inventory/confirm_delete.html', context)


# ============================================================================
# INVENTORY UPLOAD (CSV/EXCEL)
# ============================================================================

@login_required(login_url='users:login')
@role_required('pharmacist', require_verified=True)
def upload_inventory(request):
    """
    Handle bulk upload of inventory via CSV or Excel file.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        messages.error(request, "You do not have an associated pharmacy.")
        return redirect('users:login')
    
    if request.method == 'POST':
        form = InventoryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            # Process the file
            success_count, failed_count, errors = process_inventory_file(file, pharmacy, user)
            
            if failed_count > 0:
                messages.warning(
                    request,
                    f"Upload completed: {success_count} records imported, {failed_count} failed."
                )
                context = {
                    'form': form,
                    'pharmacy': pharmacy,
                    'errors': errors,
                }
                return render(request, 'inventory/upload_inventory.html', context)
            else:
                messages.success(request, f"Upload completed: {success_count} records imported successfully!")
                return redirect('inventory:dashboard')
    else:
        form = InventoryUploadForm()
    
    context = {
        'form': form,
        'pharmacy': pharmacy,
    }
    
    return render(request, 'inventory/upload_inventory.html', context)


def process_inventory_file(file, pharmacy, user):
    """
    Process uploaded CSV or Excel file and create/update inventory records.
    
    Expected columns:
    - medicine_name (required)
    - quantity (required, non-negative)
    - category (optional)
    - strength (optional)
    - active_ingredient (optional)
    - minimum_threshold (optional, non-negative)
    
    Returns:
        (success_count, failed_count, errors_list)
    """
    success_count = 0
    failed_count = 0
    errors = []
    
    # Determine file type and parse
    file_name = file.name.lower()
    
    try:
        if file_name.endswith('.csv'):
            rows = parse_csv_file(file)
        elif file_name.endswith('.xlsx'):
            if not EXCEL_SUPPORT:
                errors.append("Excel support not installed. Please upload a CSV file instead.")
                return 0, 1, errors
            rows = parse_excel_file(file)
        else:
            errors.append("Unsupported file format. Please use CSV or Excel (.xlsx).")
            return 0, 1, errors
        
        if not rows:
            errors.append("File is empty or has no valid rows.")
            return 0, 1, errors
        
        # Process each row
        with transaction.atomic():
            bulk_details = f"Bulk upload from {file.name}"
            
            for row_num, row in enumerate(rows, start=2):  # start=2 to account for header
                try:
                    # Extract and validate fields
                    medicine_name = str(row.get('medicine_name', '')).strip()
                    quantity_str = str(row.get('quantity', '0')).strip()
                    category = str(row.get('category', '')).strip()
                    strength = str(row.get('strength', '')).strip()
                    active_ingredient = str(row.get('active_ingredient', '')).strip()
                    threshold_str = str(row.get('minimum_threshold', '0')).strip()
                    
                    # Validate required field
                    if not medicine_name:
                        raise ValueError("medicine_name is required")
                    
                    # Validate numeric fields
                    try:
                        quantity = int(quantity_str)
                        minimum_threshold = int(threshold_str)
                    except ValueError:
                        raise ValueError("quantity and minimum_threshold must be numeric")
                    
                    if quantity < 0:
                        raise ValueError("quantity cannot be negative")
                    if minimum_threshold < 0:
                        raise ValueError("minimum_threshold cannot be negative")
                    
                    # Get or create medicine
                    medicine, _ = Medicine.objects.get_or_create(
                        name=medicine_name,
                        defaults={
                            'category': category,
                            'active_ingredient': active_ingredient,
                            'dosage_form': strength,
                        }
                    )
                    
                    # Get or create inventory
                    inventory, created = Inventory.objects.get_or_create(
                        pharmacy=pharmacy,
                        medicine=medicine,
                        defaults={
                            'quantity': quantity,
                            'minimum_threshold': minimum_threshold,
                        }
                    )
                    
                    if not created:
                        # Update existing
                        old_qty = inventory.quantity
                        old_threshold = inventory.minimum_threshold
                        inventory.quantity = quantity
                        inventory.minimum_threshold = minimum_threshold
                        inventory.save()
                        
                        # Audit log for update
                        create_audit_log(
                            user=user,
                            pharmacy=pharmacy,
                            medicine=medicine,
                            operation='UPDATE',
                            old_qty=old_qty,
                            new_qty=quantity,
                            old_threshold=old_threshold,
                            new_threshold=minimum_threshold,
                            details=f"Updated via bulk upload: {bulk_details}"
                        )
                    else:
                        # Audit log for create
                        create_audit_log(
                            user=user,
                            pharmacy=pharmacy,
                            medicine=medicine,
                            operation='CREATE',
                            new_qty=quantity,
                            new_threshold=minimum_threshold,
                            details=f"Created via bulk upload: {bulk_details}"
                        )
                    
                    success_count += 1
                
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Create a summary audit log for the bulk upload
            if success_count > 0:
                create_audit_log(
                    user=user,
                    pharmacy=pharmacy,
                    medicine=None,
                    operation='BULK_UPLOAD',
                    details=f"Bulk upload: {success_count} records imported from {file.name}"
                )
    
    except Exception as e:
        errors.append(f"Error processing file: {str(e)}")
        failed_count += 1
    
    return success_count, failed_count, errors


def parse_csv_file(file):
    """
    Parse a CSV file and return list of dictionaries.
    """
    rows = []
    try:
        # Decode file content
        content = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        
        if reader.fieldnames is None:
            return []
        
        for row in reader:
            rows.append(row)
    
    except Exception as e:
        raise Exception(f"Failed to parse CSV: {str(e)}")
    
    return rows


def parse_excel_file(file):
    """
    Parse an Excel file and return list of dictionaries.
    """
    rows = []
    try:
        workbook = openpyxl.load_workbook(file)
        worksheet = workbook.active
        
        # Get header row
        headers = []
        for cell in worksheet[1]:
            headers.append(cell.value)
        
        if not headers or all(h is None for h in headers):
            return []
        
        # Get data rows
        for row in worksheet.iter_rows(min_row=2, values_only=False):
            row_dict = {}
            for idx, header in enumerate(headers):
                if idx < len(row):
                    cell_value = row[idx].value
                    row_dict[header] = cell_value if cell_value is not None else ''
                else:
                    row_dict[header] = ''
            
            # Skip empty rows
            if any(row_dict.values()):
                rows.append(row_dict)
    
    except Exception as e:
        raise Exception(f"Failed to parse Excel file: {str(e)}")
    
    return rows


# ============================================================================
# AUDIT LOG VIEW
# ============================================================================

@login_required(login_url='users:login')
@role_required('pharmacist', require_verified=True)
def audit_log(request):
    """
    Display the immutable audit log for inventory changes in this pharmacy.
    Pharmacists can view but not edit/delete audit records.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        messages.error(request, "You do not have an associated pharmacy.")
        return redirect('users:login')
    
    # Get all audit logs for this pharmacy
    logs = InventoryUpdateLog.objects.filter(pharmacy=pharmacy).select_related(
        'user', 'medicine'
    ).order_by('-timestamp')
    
    context = {
        'pharmacy': pharmacy,
        'logs': logs,
    }
    
    return render(request, 'inventory/audit_log.html', context)

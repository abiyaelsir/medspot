from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.decorators import role_required
from inventory.views import get_pharmacist_pharmacy
from inventory.models import Inventory


@login_required(login_url='users:login')
@role_required("pharmacist", require_verified=True)
def pharmacist_dashboard(request):
    """
    Pharmacist dashboard - now delegates to inventory app.
    Displays inventory summary and provides access to inventory management.
    """
    user = request.user
    pharmacy = get_pharmacist_pharmacy(user)
    
    if not pharmacy:
        from django.contrib import messages
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

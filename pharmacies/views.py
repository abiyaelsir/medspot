from django.shortcuts import render
from users.decorators import pharmacist_verified_required
from users.decorators import role_required
@pharmacist_verified_required
def pharmacist_dashboard(request):
    # dashboard code...
    return render(request, "pharmacies/dashboard.html")

@role_required("pharmacist", require_verified=True)
def pharmacist_dashboard(request):
    # dashboard code...
    return render(request, "pharmacies/dashboard.html")
# name=users/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def role_required(*allowed_roles, require_verified=False, redirect_to="users:access_denied"):
    """
    Usage:
      @role_required("pharmacist", require_verified=True)
      def view(...)

    allowed_roles can be one or more role strings.
    If require_verified=True, also requires user.is_verified == True.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect("users:login")
            if user.role not in allowed_roles:
                messages.error(request, "Access denied: insufficient role.")
                return redirect(redirect_to)
            if require_verified and not getattr(user, "is_verified", False):
                messages.error(request, "Access denied: account pending approval.")
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
def pharmacist_verified_required(view_func):
    """
    Decorator for views that checks if the user is a verified pharmacist.
    """
    actual_decorator = user_passes_test(
        lambda user: user.is_authenticated and getattr(user, 'role', None) == 'pharmacist',
        login_url='users:login' # نستخدم المسار الصحيح المرفق بالـ namespace
    )
    return actual_decorator(view_func)
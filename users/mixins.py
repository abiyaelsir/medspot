#name=users/mixins.py
from django.contrib import messages
from django.shortcuts import redirect

class RoleRequiredMixin:
    """
    For class-based views. Set attributes:
      required_roles = ("pharmacist",)
      require_verified = True
      redirect_to = "users:access_denied"
    """
    required_roles = ()
    require_verified = False
    redirect_to = "users:access_denied"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            from django.shortcuts import redirect as _redirect
            return _redirect("users:login")
        if user.role not in self.required_roles:
            messages.error(request, "Access denied: insufficient role.")
            from django.shortcuts import redirect as _redirect
            return _redirect(self.redirect_to)
        if self.require_verified and not getattr(user, "is_verified", False):
            messages.error(request, "Access denied: account pending approval.")
            from django.shortcuts import redirect as _redirect
            return _redirect(self.redirect_to)
        return super().dispatch(request, *args, **kwargs)
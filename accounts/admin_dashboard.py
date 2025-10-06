from django.contrib import admin
from django.urls import path
from django.db.models import Sum, Count
from django.shortcuts import render
from django.shortcuts import redirect
from accounts.models import User
from bookings.models import Booking, Transaction
from playgrounds.models import SportVenue

class CustomAdminSite(admin.AdminSite):
    
    def index(self, request, extra_context=None):
        return redirect("admin:dashboard")


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_users = User.objects.count()
        total_venues = SportVenue.objects.count()
        total_bookings = Booking.objects.count()
        total_revenue = Transaction.objects.aggregate(total=Sum("amount"))["total"] or 0

        top_venues = (
            Booking.objects.values("stadium__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        context = {
            "total_users": total_users,
            "total_venues": total_venues,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "top_venues": top_venues,
            "title": "📊 Аналитика",
        }
        return render(request, "admin/dashboard.html", context)


custom_admin = CustomAdminSite(name="custom_admin")

for model, model_admin in admin.site._registry.items():
    custom_admin.register(model, model_admin.__class__)

from django.urls import path
from django.db.models import Sum, Count
from django.shortcuts import render, redirect
from django.contrib import admin
from unfold.sites import UnfoldAdminSite

from accounts.models import User
from bookings.models import Booking, Transaction as BookingTransaction
from playgrounds.models import SportVenue


# class CustomAdminSite(UnfoldAdminSite):
#     """Кастомная админка с дашбордом на Unfold"""

#     def index(self, request, extra_context=None):
#         return redirect("admin:dashboard")

#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
#         ]
#         return custom_urls + urls

#     def dashboard_view(self, request):
#         total_users = User.objects.count()
#         total_venues = SportVenue.objects.count()
#         total_bookings = Booking.objects.count()
#         total_revenue = BookingTransaction.objects.aggregate(total=Sum("amount"))["total"] or 0
    
#         top_venues = (
#             Booking.objects.values("stadium__name")
#             .annotate(total=Count("id"))
#             .order_by("-total")[:5]
#         )
    
#         context = {
#             "total_users": total_users,
#             "total_venues": total_venues,
#             "total_bookings": total_bookings,
#             "total_revenue": total_revenue,
#             "top_venues": top_venues,
#             "title": "📊 Аналитика",
#         }
#         return render(request, "admin/dashboard.html", context)



# custom_admin = CustomAdminSite(name="custom_admin")

# # Регистрируем все модели, чтобы не потерять существующие админки
# for model, model_admin in admin.site._registry.items():
#     custom_admin.register(model, model_admin.__class__)


from django.db.models import Count, Sum
from accounts.models import User
from playgrounds.models import SportVenue
from bookings.models import Booking, BookingTransaction

def dashboard_view(request, context=None):
    if context is None:
        context = {}

    total_users = User.objects.count()
    total_venues = SportVenue.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = BookingTransaction.objects.aggregate(total=Sum("amount"))["total"] or 0

    top_venues = (
        Booking.objects.values("stadium__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    context.update({
        "total_users": total_users,
        "total_venues": total_venues,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "top_venues": top_venues,
        "title": "📊 Аналитика",
        "SITE_TITLE": "PolyaTop Admin",
        "SITE_HEADER": "PolyaTop Панель управления",
        "SITE_SUBHEADER": "Статистика и управление",
    })

    return context

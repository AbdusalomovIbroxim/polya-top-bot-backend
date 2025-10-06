from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from bookings.models import Booking, Transaction
from accounts.models import User
from playgrounds.models import Playground
# from wallet.models import WalletTransaction
from django.db.models import Sum
from django.utils import timezone


class CustomAdminSite(AdminSite):
    site_header = "Панель управления PolyaTop"
    site_title = "Админка PolyaTop"
    index_title = "Аналитика и статистика"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="admin-dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_users = User.objects.count()
        total_bookings = Booking.objects.count()
        total_fields = Playground.objects.count()
        total_income = Transaction.objects.filter(type="income").aggregate(total=Sum("amount"))["total"] or 0

        today = timezone.now().date()
        today_bookings = Booking.objects.filter(created_at__date=today).count()

        context = dict(
            self.each_context(request),
            title="Дашборд аналитики",
            total_users=total_users,
            total_bookings=total_bookings,
            total_fields=total_fields,
            total_income=total_income,
            today_bookings=today_bookings,
        )
        return TemplateResponse(request, "admin/dashboard.html", context)

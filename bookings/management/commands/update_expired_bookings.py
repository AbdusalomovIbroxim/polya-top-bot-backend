from django.core.management.base import BaseCommand
from bookings.models import Booking
from django.utils import timezone


class Command(BaseCommand):
    help = 'Обновляет статус всех истекших броней на EXPIRED'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать количество броней, которые будут обновлены, без выполнения',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Находим все истекшие брони
        expired_bookings = Booking.objects.filter(
            end_time__lt=now,
            status__in=['PENDING', 'CONFIRMED']
        )
        
        count = expired_bookings.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'Найдено {count} истекших броней (dry-run)'
                )
            )
            return
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Нет истекших броней для обновления')
            )
            return
        
        # Обновляем статус
        updated_count = expired_bookings.update(
            status='EXPIRED',
            updated_at=now
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно обновлено {updated_count} истекших броней'
            )
        ) 
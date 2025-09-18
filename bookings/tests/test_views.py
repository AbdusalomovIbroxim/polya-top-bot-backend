import json
import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from bookings.models import Booking, Transaction
from stadiums.models import Stadium

# Импортируем фабрики, чтобы избежать дублирования кода для создания тестовых данных
from .factories import UserFactory, StadiumFactory, BookingFactory, TransactionFactory

User = get_user_model()


@pytest.mark.django_db
class BookingViewSetTests(APITestCase):
    """Тестирование ViewSet для модели Booking."""
    
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.stadium = StadiumFactory()
        self.list_url = reverse('booking-list')
        
    def test_create_booking_authenticated(self):
        """Проверка, что аутентифицированный пользователь может создать бронь."""
        data = {
            'stadium': self.stadium.id,
            'start_time': (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timezone.timedelta(days=2, hours=2)).isoformat(),
            'amount': Decimal('100000.00'),
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.first().user, self.user)
        self.assertEqual(Booking.objects.first().status, Booking.STATUS_PENDING)
    
    def test_list_bookings_only_user_data(self):
        """Проверка, что пользователь видит только свои брони."""
        BookingFactory(user=self.user)
        BookingFactory(user=UserFactory())
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['stadium'], self.stadium.id)

    def test_pay_cash_action_creates_pending_transaction(self):
        """Тестирование оплаты наличными."""
        booking = BookingFactory(user=self.user)
        pay_url = reverse('booking-pay', kwargs={'pk': booking.id})
        data = {'payment_method': Booking.PAYMENT_CASH}
        
        response = self.client.post(pay_url, data, format='json')
        booking.refresh_from_db()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(booking.payment_method, Booking.PAYMENT_CASH)
        self.assertTrue(Transaction.objects.filter(booking=booking, provider="cash", status="pending").exists())
        self.assertIn("Вы выбрали оплату наличными", response.data['detail'])
        
    def test_pay_card_action_returns_payment_url(self):
        """Тестирование оплаты картой (Click) возвращает URL."""
        booking = BookingFactory(user=self.user)
        pay_url = reverse('booking-pay', kwargs={'pk': booking.id})
        data = {'payment_method': Booking.PAYMENT_CARD}
        
        response = self.client.post(pay_url, data, format='json')
        booking.refresh_from_db()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(booking.payment_method, Booking.PAYMENT_CARD)
        self.assertTrue(Transaction.objects.filter(booking=booking, provider="click", status="pending").exists())
        self.assertIn('payment_url', response.data)
        
    def test_pay_on_processed_booking_fails(self):
        """Проверка, что нельзя оплатить уже обработанную бронь."""
        booking = BookingFactory(user=self.user, status=Booking.STATUS_CONFIRMED)
        pay_url = reverse('booking-pay', kwargs={'pk': booking.id})
        data = {'payment_method': Booking.PAYMENT_CASH}
        
        response = self.client.post(pay_url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Бронь уже обработана", response.data['detail'])
        
    def test_expired_action_marks_expired_bookings(self):
        """Тестирование обновления статуса на "просрочено"."""
        expired_booking = BookingFactory(user=self.user, end_time=timezone.now() - timezone.timedelta(hours=1))
        active_booking = BookingFactory(user=self.user)
        
        expired_url = reverse('booking-expired')
        response = self.client.get(expired_url)
        
        self.assertEqual(response.status_code, 200)
        expired_booking.refresh_from_db()
        active_booking.refresh_from_db()
        
        self.assertEqual(expired_booking.status, Booking.STATUS_EXPIRED)
        self.assertEqual(active_booking.status, Booking.STATUS_PENDING)


@pytest.mark.django_db
class TransactionViewSetTests(APITestCase):
    """Тестирование ViewSet для модели Transaction."""
    
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('transaction-list')
        
    def test_list_transactions(self):
        """Проверка, что пользователь видит только свои транзакции."""
        TransactionFactory(user=self.user)
        TransactionFactory(user=UserFactory())
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user.id)
        
    def test_retrieve_transaction(self):
        """Проверка, что пользователь может получить свою транзакцию."""
        transaction_obj = TransactionFactory(user=self.user)
        detail_url = reverse('transaction-detail', kwargs={'pk': transaction_obj.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], transaction_obj.id)
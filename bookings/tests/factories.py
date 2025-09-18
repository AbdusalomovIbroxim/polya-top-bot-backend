import factory
from django.contrib.auth import get_user_model
from bookings.models import Booking, Transaction
from stadiums.models import Stadium
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@test.com')
    telegram_username = factory.Sequence(lambda n: f'tg_user{n}')
    phone = factory.Sequence(lambda n: f'9989000000{n}')


class StadiumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stadium
    
    name = factory.Sequence(lambda n: f'Stadium {n}')
    price_per_hour = Decimal('100000.00')
    capacity = 10


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Booking
    
    user = factory.SubFactory(UserFactory)
    stadium = factory.SubFactory(StadiumFactory)
    start_time = timezone.now() + timezone.timedelta(days=1)
    end_time = factory.LazyAttribute(lambda o: o.start_time + timezone.timedelta(hours=2))
    amount = factory.LazyAttribute(lambda o: o.stadium.price_per_hour * Decimal(2))
    status = Booking.STATUS_PENDING


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction
    
    booking = factory.SubFactory(BookingFactory)
    user = factory.LazyAttribute(lambda o: o.booking.user)
    provider = "click"
    amount = factory.LazyAttribute(lambda o: o.booking.amount)
    status = "pending"
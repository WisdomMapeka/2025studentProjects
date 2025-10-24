from django.test import TestCase

# Create your tests here.
import uuid
from datetime import date, time
from django.test import TestCase
from django.utils import timezone
from bookings.models import Booking
from waiting_queues.models import WaitingQueue
from core.models import User, Service, Branch


class BookingModelTest(TestCase):

    def setUp(self):
        # Create sample related objects
        self.user = User.objects.create(username="testuser", password="testpass")
        self.service = Service.objects.create(name="Passport Renewal")
        self.branch = Branch.objects.create(name="Harare Central")

    def test_booking_saves_and_generates_token(self):
        """Booking should automatically generate a unique token when saved."""
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(10, 0)
        )

        self.assertIsNotNone(booking.token_number)
        self.assertTrue(booking.token_number.startswith("TOKEN-"))
        self.assertEqual(booking.status, "pending")
        self.assertEqual(booking.priority, "normal")

    def test_token_is_unique(self):
        """Each Booking should have a unique token_number."""
        b1 = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(10, 0)
        )
        b2 = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(11, 0)
        )
        self.assertNotEqual(b1.token_number, b2.token_number)

    def test_str_representation(self):
        """__str__ should return a readable representation."""
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(10, 0)
        )
        expected_str = f"Booking {booking.token_number} - {self.user.username}"
        self.assertEqual(str(booking), expected_str)

    def test_can_save_with_custom_token(self):
        """If token_number is provided, it should not auto-generate a new one."""
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(9, 30),
            token_number="TOKEN-MANUAL-12345"
        )
        self.assertEqual(booking.token_number, "TOKEN-MANUAL-12345")

    def test_generate_unique_token_format(self):
        """Generated token should follow the pattern TOKEN-YYYYMMDD-XXXXX."""
        token = Booking.generate_unique_token()
        today = timezone.now().strftime("%Y%m%d")
        self.assertTrue(token.startswith(f"TOKEN-{today}-"))
        self.assertEqual(len(token.split("-")[-1]), 5)  # random part length

    def test_ordering_by_date_and_time(self):
        """Bookings should be ordered by date and time."""
        b1 = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date(2025, 10, 20),
            booking_time=time(9, 0)
        )
        b2 = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date(2025, 10, 21),
            booking_time=time(8, 0)
        )
        bookings = list(Booking.objects.all())
        self.assertEqual(bookings, [b1, b2])

    # ✅ NEW TESTS BELOW ---------------------------------------------------------

    def test_waiting_queue_created_on_booking_save(self):
        """A WaitingQueue entry should automatically be created when a Booking is saved."""
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(10, 0)
        )

        queue_entry = WaitingQueue.objects.filter(booking=booking).first()
        self.assertIsNotNone(queue_entry, "WaitingQueue entry was not created by signal")
        self.assertEqual(queue_entry.booking, booking)
        self.assertEqual(queue_entry.status, "waiting")
        self.assertEqual(queue_entry.booked_date, booking.booking_date)
        self.assertEqual(queue_entry.booked_time, booking.booking_time)

    def test_waiting_queue_not_duplicated_on_booking_update(self):
        """Updating an existing Booking should not create a duplicate WaitingQueue entry."""
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            booking_time=time(10, 0)
        )

        # Update the booking (signal should not create another queue entry)
        booking.status = "confirmed"
        booking.save()

        queue_entries = WaitingQueue.objects.filter(booking=booking)
        self.assertEqual(queue_entries.count(), 1, "Duplicate WaitingQueue entry created on update")

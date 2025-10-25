# bookings/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
import uuid

# Import your models
from core.models import Service, Branch
from bookings.models import Booking
from waiting_queues.models import WaitingQueue, Counter


class BookingModelTest(TestCase):
    def setUp(self):
        """Set up test data for all tests"""
        User = get_user_model()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='citizen'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Tax Filing',
            description='Income tax filing service',
            estimated_duration=30
        )
        
        # Create test branch
        self.branch = Branch.objects.create(
            name='Main Branch',
            address='123 Main St',
            phone_number='+263123456789'
        )
        
        # Common booking data
        self.booking_data = {
            'citizen': self.user,
            'service': self.service,
            'branch': self.branch,
            'booking_date': date.today() + timedelta(days=1),
            'booking_time': time(10, 0),
            'status': 'pending',
            'priority': 'normal'
        }

    def test_create_booking_with_minimal_data(self):
        """Test creating a booking with only required fields"""
        booking = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1)
        )
        
        self.assertIsNotNone(booking.id)
        self.assertIsNotNone(booking.token_number)
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.priority, 'normal')
        self.assertTrue(isinstance(booking.id, uuid.UUID))

    def test_create_booking_with_all_fields(self):
        """Test creating a booking with all fields"""
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today() + timedelta(days=1),
            booking_time=time(10, 0),
            status='confirmed',
            priority='priority',
            special_requirements='Wheelchair access required',
            estimated_wait_time=15
        )
        
        self.assertEqual(booking.citizen, self.user)
        self.assertEqual(booking.service, self.service)
        self.assertEqual(booking.branch, self.branch)
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(booking.priority, 'priority')
        self.assertEqual(booking.special_requirements, 'Wheelchair access required')
        self.assertEqual(booking.estimated_wait_time, 15)

    def test_token_number_generation(self):
        """Test that token number is automatically generated"""
        booking = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1)
        )
        
        self.assertIsNotNone(booking.token_number)
        self.assertTrue(booking.token_number.startswith('TOKEN-'))
        
        # Test that token is unique
        booking2 = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1)
        )
        
        self.assertNotEqual(booking.token_number, booking2.token_number)

    def test_booking_string_representation(self):
        """Test the string representation of Booking"""
        booking = Booking.objects.create(
            citizen=self.user,
            booking_date=date.today() + timedelta(days=1)
        )
        
        expected_str = f"Booking {booking.token_number} - {self.user.username}"
        self.assertEqual(str(booking), expected_str)

    def test_booking_ordering(self):
        """Test that bookings are ordered by date and time"""
        # Create bookings with different dates and times
        booking1 = Booking.objects.create(
            booking_date=date.today() + timedelta(days=2),
            booking_time=time(9, 0)
        )
        
        booking2 = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1),
            booking_time=time(11, 0)
        )
        
        booking3 = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1),
            booking_time=time(10, 0)
        )
        
        bookings = Booking.objects.all()
        
        # Should be ordered by date (ascending) then time (ascending)
        self.assertEqual(bookings[0], booking3)  # Same day, earlier time
        self.assertEqual(bookings[1], booking2)  # Same day, later time
        self.assertEqual(bookings[2], booking1)  # Later day

    def test_booking_status_choices(self):
        """Test booking status choices"""
        booking = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1)
        )
        
        # Test valid statuses
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']
        for status in valid_statuses:
            booking.status = status
            booking.save()
            self.assertEqual(booking.status, status)

    def test_booking_priority_choices(self):
        """Test booking priority choices"""
        booking = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1)
        )
        
        # Test valid priorities
        valid_priorities = ['normal', 'priority', 'vip']
        for priority in valid_priorities:
            booking.priority = priority
            booking.save()
            self.assertEqual(booking.priority, priority)

    def test_booking_meta_indexes(self):
        """Test that the correct database indexes are set"""
        indexes = [index.fields for index in Booking._meta.indexes]
        
        self.assertIn(['booking_date', 'status'], indexes)
        self.assertIn(['citizen', 'status'], indexes)

    def test_auto_timestamps(self):
        """Test that created_at and updated_at are automatically set"""
        booking = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1)
        )
        
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)
        
        # Instead of checking exact equality (which can fail due to microseconds),
        # check that they are very close (within 1 second)
        time_difference = abs((booking.created_at - booking.updated_at).total_seconds())
        self.assertLessEqual(time_difference, 1.0)
        
        # Test that updated_at changes on save
        original_updated_at = booking.updated_at
        booking.status = 'confirmed'
        booking.save()
        
        self.assertNotEqual(booking.updated_at, original_updated_at)
        self.assertGreater(booking.updated_at, original_updated_at)

    def test_booking_with_null_optional_fields(self):
        """Test creating a booking with null optional fields"""
        booking = Booking.objects.create(
            booking_date=date.today() + timedelta(days=1),
            citizen=None,
            service=None,
            branch=None,
            booking_time=None,
            special_requirements=None
        )
        
        self.assertIsNone(booking.citizen)
        self.assertIsNone(booking.service)
        self.assertIsNone(booking.branch)
        self.assertIsNone(booking.booking_time)
        self.assertIsNone(booking.special_requirements)


class BookingSignalTest(TestCase):
    def setUp(self):
        """Set up test data for signal tests"""
        User = get_user_model()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='citizen'
        )
        
        self.service = Service.objects.create(
            name='Tax Consultation',
            description='Tax consultation service'
        )
        
        self.branch = Branch.objects.create(
            name='Downtown Branch',
            address='456 Downtown St'
        )

    def test_waiting_queue_creation_on_booking_creation(self):
        """Test that WaitingQueue entry is created when Booking is created"""
        # Verify no waiting queue entries exist
        self.assertEqual(WaitingQueue.objects.count(), 0)
        
        # Create a booking
        booking = Booking.objects.create(
            citizen=self.user,
            service=self.service,
            branch=self.branch,
            booking_date=date.today() + timedelta(days=1),
            booking_time=time(14, 30)
        )
        
        # Verify waiting queue entry was created
        self.assertEqual(WaitingQueue.objects.count(), 1)
        
        waiting_queue_entry = WaitingQueue.objects.first()
        self.assertEqual(waiting_queue_entry.booking, booking)
        self.assertEqual(waiting_queue_entry.booked_date, booking.booking_date)
        self.assertEqual(waiting_queue_entry.booked_time, booking.booking_time)
        self.assertEqual(waiting_queue_entry.status, 'waiting')

    def test_no_waiting_queue_creation_on_booking_update(self):
        """Test that WaitingQueue entry is not created when Booking is updated"""
        # Create a booking
        booking = Booking.objects.create(
            citizen=self.user,
            booking_date=date.today() + timedelta(days=1)
        )
        
        # Verify waiting queue entry was created
        self.assertEqual(WaitingQueue.objects.count(), 1)
        
        # Update the booking
        booking.status = 'confirmed'
        booking.save()
        
        # Verify no new waiting queue entry was created
        self.assertEqual(WaitingQueue.objects.count(), 1)

    def test_multiple_bookings_create_multiple_waiting_queues(self):
        """Test that multiple bookings create multiple waiting queue entries"""
        User = get_user_model()
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            user_type='citizen'
        )
        
        # Create first booking
        booking1 = Booking.objects.create(
            citizen=self.user,
            booking_date=date.today() + timedelta(days=1),
            booking_time=time(10, 0)
        )
        
        # Create second booking
        booking2 = Booking.objects.create(
            citizen=user2,
            booking_date=date.today() + timedelta(days=1),
            booking_time=time(11, 0)
        )
        
        # Verify two waiting queue entries were created
        self.assertEqual(WaitingQueue.objects.count(), 2)
        
        waiting_queues = WaitingQueue.objects.all()
        self.assertEqual(waiting_queues[0].booking, booking1)
        self.assertEqual(waiting_queues[1].booking, booking2)


class BookingQueryTest(TestCase):
    def setUp(self):
        """Set up test data for query tests"""
        User = get_user_model()
        
        self.user1 = User.objects.create_user(
            username='user1', 
            email='user1@example.com',
            password='pass123',
            user_type='citizen'
        )
        self.user2 = User.objects.create_user(
            username='user2', 
            email='user2@example.com',
            password='pass123',
            user_type='citizen'
        )
        
        self.service = Service.objects.create(name='Test Service')
        self.branch = Branch.objects.create(name='Test Branch')
        
        # Create bookings with different statuses and dates
        self.booking1 = Booking.objects.create(
            citizen=self.user1,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            status='pending'
        )
        
        self.booking2 = Booking.objects.create(
            citizen=self.user1,
            service=self.service,
            branch=self.branch,
            booking_date=date.today() + timedelta(days=1),
            status='confirmed'
        )
        
        self.booking3 = Booking.objects.create(
            citizen=self.user2,
            service=self.service,
            branch=self.branch,
            booking_date=date.today(),
            status='completed'
        )

    def test_filter_by_status(self):
        """Test filtering bookings by status"""
        pending_bookings = Booking.objects.filter(status='pending')
        self.assertEqual(pending_bookings.count(), 1)
        self.assertEqual(pending_bookings.first(), self.booking1)
        
        confirmed_bookings = Booking.objects.filter(status='confirmed')
        self.assertEqual(confirmed_bookings.count(), 1)
        self.assertEqual(confirmed_bookings.first(), self.booking2)

    def test_filter_by_citizen_and_status(self):
        """Test filtering by citizen and status combination"""
        user1_pending = Booking.objects.filter(citizen=self.user1, status='pending')
        self.assertEqual(user1_pending.count(), 1)
        self.assertEqual(user1_pending.first(), self.booking1)
        
        user1_completed = Booking.objects.filter(citizen=self.user1, status='completed')
        self.assertEqual(user1_completed.count(), 0)

    def test_filter_by_booking_date(self):
        """Test filtering by booking date"""
        today_bookings = Booking.objects.filter(booking_date=date.today())
        self.assertEqual(today_bookings.count(), 2)  # booking1 and booking3
        
        tomorrow_bookings = Booking.objects.filter(booking_date=date.today() + timedelta(days=1))
        self.assertEqual(tomorrow_bookings.count(), 1)
        self.assertEqual(tomorrow_bookings.first(), self.booking2)


class EdgeCasesTest(TestCase):
    def test_booking_with_past_date(self):
        """Test creating a booking with a past date (should be allowed)"""
        past_date = date.today() - timedelta(days=1)
        booking = Booking.objects.create(booking_date=past_date)
        
        self.assertEqual(booking.booking_date, past_date)

    def test_duplicate_token_number_prevention(self):
        """Test that token number generation prevents duplicates"""
        import bookings.models
        
        # Mock the random generation to test uniqueness
        original_generate_unique_token = bookings.models.Booking.generate_unique_token
        
        # Create a scenario where duplicate tokens would be generated
        test_token = "TOKEN-20251024-TEST1"
        generated_tokens = [test_token, test_token, "TOKEN-20251024-TEST2"]
        
        def mock_generate():
            return generated_tokens.pop(0)
        
        bookings.models.Booking.generate_unique_token = staticmethod(mock_generate)
        
        try:
            # Create first booking
            booking1 = Booking.objects.create(booking_date=date.today())
            self.assertEqual(booking1.token_number, test_token)
            
            # Create second booking - should get a different token after collision
            booking2 = Booking.objects.create(booking_date=date.today())
            self.assertEqual(booking2.token_number, "TOKEN-20251024-TEST2")
        finally:
            # Restore original method
            bookings.models.Booking.generate_unique_token = original_generate_unique_token


# Simple test to verify the test setup is working
class SimpleTestCase(TestCase):
    def test_basic_addition(self):
        """Basic test to verify tests are running"""
        self.assertEqual(1 + 1, 2)
    
    def test_imports_working(self):
        """Test that all imports are working correctly"""
        # This will fail if imports are broken
        from core.models import User, Service, Branch
        from bookings.models import Booking
        from waiting_queues.models import WaitingQueue
        
        self.assertTrue(True)  # If we get here, imports work
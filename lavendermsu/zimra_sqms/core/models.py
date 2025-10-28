import uuid
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('citizen', 'Citizen'),
        ('staff', 'Staff'),
        ('admin', 'Administrator'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='citizen', blank=True, null=True)
    tin = models.CharField(max_length=20, blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=15, help_text="Include country code, e.g., 263777123123")
    id_number = models.CharField(max_length=20, default='id-num', help_text="National ID or Passport Number eg 22-88888z33")
    email = models.EmailField(unique=True, default='user@g.com')
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        if not self.tin:
            self.tin = self.generate_unique_tin(self)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_tin(user=None):
        """
        Generates a unique identifier for a user.
        - Citizens get a TIN (Tax Identification Number)
        - Staff, Superusers, and Admins get an SID (Staff Identification Number)
        Format examples:
          TIN-20251028-AB12C3
          SID-20251028-XY89Z0
        """

        # Determine prefix
        if user and (user.is_staff or user.is_superuser or user.user_type in ['staff', 'admin']):
            prefix = "SID"
        else:
            prefix = "TIN"

        # Generate date + random part
        date_part = timezone.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        code_candidate = f"{prefix}-{date_part}-{random_part}"

        # Ensure uniqueness
        while User.objects.filter(tin=code_candidate).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            code_candidate = f"{prefix}-{date_part}-{random_part}"

        return code_candidate





class Service(models.Model):
    SERVICE_CATEGORIES = (
        ('tax', 'Tax Services'),
        ('customs', 'Customs Services'),
        ('trade', 'Trade Facilitation'),
        ('travel', 'Travel Services'),
        ('other', 'Other Services'),
    )
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes", blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    operating_hours = models.TextField(help_text="Operating hours description", blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Counter(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
    number = models.PositiveIntegerField(blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, blank=True, null=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('branch', 'number')
    
    def __str__(self):
        return f"Counter {self.number} - {self.branch.name}"
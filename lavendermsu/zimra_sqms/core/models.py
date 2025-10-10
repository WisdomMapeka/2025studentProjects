from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('citizen', 'Citizen'),
        ('staff', 'Staff'),
        ('admin', 'Administrator'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='citizen', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # 🆕
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"



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
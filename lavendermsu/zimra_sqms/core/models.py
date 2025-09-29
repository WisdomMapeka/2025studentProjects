from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('citizen', 'Citizen'),
        ('staff', 'Staff'),
        ('admin', 'Administrator'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='citizen')
    phone_number = models.CharField(max_length=15, blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES)
    description = models.TextField()
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    operating_hours = models.TextField(help_text="Operating hours description")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Counter(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('branch', 'number')
    
    def __str__(self):
        return f"Counter {self.number} - {self.branch.name}"
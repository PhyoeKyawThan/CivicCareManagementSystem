import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    
    # Email should be required and unique
    email = models.EmailField(max_length=200, unique=True, null=False, blank=False)
    
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Changed to DateField
    date_of_birth = models.DateField(null=True, blank=True)  # Use DateField, not DateTimeField
    
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('administrator', 'Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    # Add username field as not required if you want email-based auth
    username = models.CharField(max_length=150, unique=True)

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['username', 'full_name']  # Fields required when creating superuser

    def __str__(self):
        return self.email  # Or self.username
    
    def save(self, *args, **kwargs):
        # Ensure email is lowercase
        self.email = self.email.lower()
        super().save(*args, **kwargs)
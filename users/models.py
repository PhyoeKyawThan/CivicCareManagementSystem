import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings


class PushToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="push_tokens"
    )

    fcm_token = models.CharField(max_length=255, unique=True)

    device_type = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"



class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    
    email = models.EmailField(max_length=200, unique=True, null=False, blank=False)
    
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    date_of_birth = models.DateField(null=True, blank=True) 
    
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('administrator', 'Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    username = models.CharField(max_length=150, unique=True)

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['username', 'full_name']  

    def __str__(self):
        return self.email 
    
    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
import uuid
from django.db import models
from django.conf import settings
from issues.models import Issue

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions_triggered"
    )
    title = models.CharField(max_length=255)
    
    body = models.TextField() 
    ref_url = models.CharField(max_length=500, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Matches data?: string (Stores JSON for deep linking)
    data = models.JSONField(null=True, blank=True)

    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True  
    )
    
    EVENT_TYPES = (
        ('citizen_issue_reported', 'Issue Reported'),
        ('citizen_issue_resolved', 'Issue Resolved'),
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
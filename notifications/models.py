from django.db import models
from issues.models import Issue
from django.conf import settings
import uuid

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
  
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField() 
    
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True  
    )
    
    NOTIFICATION_CATEGORIES = (
        ('environmental', 'Environmental Development'),
        ('public_service', 'Public Service Request'),
        ('community', 'Community Announcement'),
        ('system', 'System Notification'),
    )
    category = models.CharField(max_length=50, choices=NOTIFICATION_CATEGORIES, default='system')
    
    EVENT_TYPES = (
        # Citizen-facing events
        ('citizen_issue_reported', 'Issue Reported'),
        ('citizen_issue_accepted', 'Issue Accepted'),
        ('citizen_issue_in_progress', 'Issue In Progress'),
        ('citizen_issue_resolved', 'Issue Resolved'),
        ('citizen_comment_added', 'Comment Added'),
        ('citizen_survey_request', 'Survey Request'),
        
        # Authority-facing events
        ('authority_new_assignment', 'New Assignment'),
        ('authority_escalation', 'Issue Escalated'),
        ('authority_deadline_warning', 'Deadline Warning'),
        ('authority_performance_alert', 'Performance Alert'),
        
        # Community events
        ('community_announcement', 'Community Announcement'),
        ('community_event', 'Community Event'),
        ('volunteer_opportunity', 'Volunteer Opportunity'),
        
        # System events
        ('welcome_message', 'Welcome Message'),
        ('account_verified', 'Account Verified'),
        ('weekly_summary', 'Weekly Summary'),
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    department = models.CharField(max_length=100, null=True, blank=True)  # Which department/authority
    ward_area = models.CharField(max_length=100, null=True, blank=True)   # Which ward/area
    urgency_level = models.IntegerField(default=1)  # 1-5 scale for urgency
    
    # Delivery tracking
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)  # For authorities to acknowledge receipt
    
    # Response tracking (for authorities)
    requires_response = models.BooleanField(default=False)
    response_deadline = models.DateTimeField(null=True, blank=True)
    
    # Feedback/satisfaction (for citizens)
    satisfaction_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    feedback_provided = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Auto-remove old notifications
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['ward_area', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user.username}"
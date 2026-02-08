from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from notifications.models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    queryset = Notification.objects.all()

    def get_queryset(self):
        """
        Ensure users only see notifications sent to THEM.
        """
        return self.queryset.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        """
        Endpoint: POST /api/v1/notifications/mark-all-as-read/
        """
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.count()
        
        # Perform bulk update for efficiency
        notifications.update(is_read=True, read_at=timezone.now())
        
        return Response(
            {"message": f"Updated {count} notifications."}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """
        Endpoint: POST /api/v1/notifications/{id}/mark-as-read/
        """
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
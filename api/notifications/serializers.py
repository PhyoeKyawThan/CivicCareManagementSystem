from rest_framework import serializers
from django.contrib.auth import get_user_model
from notifications.models import Notification
from django.utils import timezone

User = get_user_model()

class NotificationUserSerializer(serializers.ModelSerializer):
    """
    Nested serializer to match the 'NotificationUser' TypeScript interface.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'avatar', 'email', 'username', 'full_name']

    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

class NotificationSerializer(serializers.ModelSerializer):
    user = NotificationUserSerializer(source='actor', read_only=True)
    type = serializers.CharField(source='event_type')

    class Meta:
        model = Notification
        fields = [
            'id', 
            'user', 
            'title', 
            'body', 
            'ref_url', 
            'type', 
            'is_read', 
            'created_at', 
            'read_at', 
            'data',
            'actor', 
            'event_type' 
        ]

        extra_kwargs = {
            'actor': {'write_only': True, 'required': False},
            'event_type': {'write_only': True},
        }

    def create(self, validated_data):
        """
        Creates a notification. Usually triggered by a service or signal.
        """
        return Notification.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Handles updating the notification, specifically the 'is_read' status.
        """
        was_read_already = instance.is_read
        is_reading_now = validated_data.get('is_read', was_read_already)

        if is_reading_now and not was_read_already:
            instance.read_at = timezone.now()
        elif not is_reading_now:
            instance.read_at = None

        return super().update(instance, validated_data)

    def validate_is_read(self, value):
        """
        Optional: Ensure once a notification is read, 
        """
        return value
from . import consumer
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumer.NotificationConsumer.as_asgi())
]
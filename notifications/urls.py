from django.urls import path
from . import views
urlpatterns = [
    path('noti', views.send_notification_view, name="noti.view")
]
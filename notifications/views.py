from django.shortcuts import render
from django.http import HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification_view(request):
    if request.method == "POST":
        message = request.POST.get('notification_text')
        user_id = request.POST.get('user')
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "send_notification", 
                "notification": message,
            }
        )
        return HttpResponse(f"Notification sent to User {user_id}!")

    return render(request, "notification.html")
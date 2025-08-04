from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/messages/notifications/$', consumers.MessageNotificationConsumer.as_asgi()),
]
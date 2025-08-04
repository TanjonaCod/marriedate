from django.urls import path
from .views import *

urlpatterns = [
    path("messages/<int:membre_id>/", aff_message, name="message_priver"),
    path("messages/delete/<int:message_id>/", delete_message, name="delete_message"),
    path("messages/delete_all/<int:membre_id>/", delete_all_messages, name="delete_all_messages"),
    path("messages/", messages_tous, name="messages_tous"),
    path("andrana/", andrana, name="andrana"),
]

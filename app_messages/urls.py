from django.urls import path
from .views import *
from .views import messages_unread_count

urlpatterns = [
    path("messages/<int:membre_id>/", aff_message, name="message_priver"),
    path("messages/delete/<int:message_id>/", delete_message, name="delete_message"),
    path("messages/delete_all/<int:membre_id>/", delete_all_messages, name="delete_all_messages"),
    path("messages/",messages_tous,name="messages_tous"),
    path('envoyer_photo/<int:membre_id>',envoyer_photo,name="envoyer_photo"),
    path("messages/received/<int:membre_id>/", get_received_messages, name="get_received_messages"),
    path("messages/send/<int:membre_id>/", send_message, name="send_message"),
    path('messages/unread_count/', messages_unread_count, name='messages_unread_count'),
    path('messages/delete_selected/', delete_selected_messages, name='delete_selected_messages'),
    path('messages/validation_photo/',validation_photo,name="validation_photo")
]

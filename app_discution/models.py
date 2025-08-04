from django.db import models
from app_membres.models import Member

class Message(models.Model):
    sender = models.ForeignKey(Member, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(Member, related_name="received_messages", on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="static/images/messages/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.pseudo} to {self.receiver.pseudo}"
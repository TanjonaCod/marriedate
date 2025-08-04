from django.db import models
from app_membres.models import Member


class Message(models.Model):
    sender = models.ForeignKey(Member, related_name="sent_messages", on_delete=models.CASCADE,null=True)
    receiver = models.ForeignKey(Member, related_name="received_messages", on_delete=models.CASCADE,null=True)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="static/images/messages/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    deleted_for = models.ManyToManyField('app_membres.Member', blank=True, related_name='deleted_messages')
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender.pseudo} to {self.receiver.pseudo}"


class Photo(models.Model):
    membre_nom = models.ForeignKey(Member, on_delete=models.CASCADE, null=True)
    images = models.ImageField(upload_to="static/images/validation_messages")
    date = models.DateTimeField(auto_now_add=True)
    valider = models.BooleanField(default=False)  # Indicates if the selfie is validated

    def __str__(self):
        return f"{self.membre_nom.pseudo}"



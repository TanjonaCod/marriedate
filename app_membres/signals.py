from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member

@receiver(post_save, sender=Member)
def set_active_member(sender, instance, **kwargs):
    if instance.is_active:
        # Désactiver les autres membres
        Member.objects.exclude(id=instance.id).update(is_active=False)

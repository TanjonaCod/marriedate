from app_membres.models import Notification, Member
from app_messages.models import Message

def notifications_count(request):
    if request.user.is_authenticated and hasattr(request.user, 'member'):
        count = Notification.objects.filter(recipient=request.user.member, is_read=False).count()
        return {'notifications_count': count}
    elif request.session.get('client'):
        try:
            member_id = request.session['client'].get('id')
            if member_id:
                count = Notification.objects.filter(recipient_id=member_id, is_read=False).count()
                return {'notifications_count': count}
        except Exception:
            pass
    return {'notifications_count': 0}

def messages_unread_senders_count(request):
    count = 0
    member_id = None
    if request.user.is_authenticated and hasattr(request.user, 'member'):
        member_id = request.user.member.id
    elif request.session.get('client'):
        member_id = request.session['client'].get('id')
    if member_id:
        # Nombre d'expéditeurs uniques ayant envoyé des messages non lus
        count = Message.objects.filter(receiver_id=member_id, is_read=False).values('sender_id').distinct().count()
    return {'messages_unread_senders_count': count}

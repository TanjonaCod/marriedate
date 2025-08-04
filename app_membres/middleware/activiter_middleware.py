from django.utils.timezone import now
from app_membres.models import Member

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client = request.session.get("client")
        if client:
            member_id = client.get("id")
            if member_id:
                try:
                    member = Member.objects.get(id=member_id)
                    member.activiter_dernier = now()
                    member.save(update_fields=["activiter_dernier"])
                except Member.DoesNotExist:
                    pass
        return self.get_response(request)


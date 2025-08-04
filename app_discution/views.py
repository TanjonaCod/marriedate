from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from app_membres.models import Member
from .models import Message
from django.db.models import Q
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist

# def get_messages(request, membre_id):
#     try:
#         # Récupérer l'objet membre
#         member = get_object_or_404(Member, id=membre_id)
#         user = Member.objects.get(id=request.session["client"]["id"])

#         # Récupérer les messages entre les deux membres
#         messages = Message.objects.filter(
#             (Q(sender=user) & Q(receiver=member)) | (Q(sender=member) & Q(receiver=user))
#         ).order_by('timestamp')

#         # Si aucun message n'est trouvé, renvoyer une réponse vide
#         if not messages:
#             return JsonResponse({'messages': []})

#         # Préparer les données des messages pour la réponse JSON
#         messages_data = []
#         for message in messages:
#             messages_data.append({
#                 'content': message.content,
#                 'image_url': message.image.url if message.image else None,
#                 'timestamp': message.timestamp.strftime('%H:%M'),
#                 'sender': message.sender.pseudo,
#             })

#         # Retourner une réponse JSON avec les messages
#         return JsonResponse({'messages': messages_data})

#     except ObjectDoesNotExist:
#         return JsonResponse({'error': 'Member or user not found'}, status=404)
#     except Exception as e:
#         # Log de l'erreur
#         print(f"Error: {e}")
#         return JsonResponse({'error': 'Internal Server Error'}, status=500)

def aff_message(request,membre_id):
    member = get_object_or_404(Member, id=membre_id)
    user = Member.objects.get(id=request.session["client"]["id"])

    if request.method == "POST":
        content = request.POST.get("message", "")
        image = request.FILES.get("image")
        message = Message.objects.create(sender=user, receiver=member, content=content, image=image)

        # Return JSON response for AJAX
        return JsonResponse({
            'success': True,
            'message': {
                'content': message.content,
                'image_url': message.image.url if message.image else None,  # Handle None case
                'timestamp': message.timestamp.strftime('%H:%M'),
            }
        })

    messages = Message.objects.filter(
        (Q(sender=user) & Q(receiver=member)) | (Q(sender=member) & Q(receiver=user))
    ).order_by('timestamp')

    return render(request, "message_priver.html", {"member": member, "messages": messages})

@csrf_exempt
def delete_message(request, message_id):
    if request.method == "DELETE":
        try:
            message = Message.objects.get(id=message_id)
            if message.sender.id == request.session["client"]["id"]:  # Ensure only the sender can delete the message
                message.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def delete_all_messages(request, membre_id):
    if request.method == "DELETE":
        try:
            user = Member.objects.get(id=request.session["client"]["id"])
            member = Member.objects.get(id=membre_id)
            Message.objects.filter(
                (Q(sender=user) & Q(receiver=member)) | (Q(sender=member) & Q(receiver=user))
            ).delete()
            return JsonResponse({'success': True})
        except Member.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Member not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def messages_tous(request):
    membre_connecte = request.session["client"]["id"]  
    derniers_messages = (
        Message.objects.filter(receiver=membre_connecte) 
        .values('sender')  
        .annotate(last_message_time=Max('timestamp'))  
        .order_by('-last_message_time')  
    )

    
    messages_complets = [
        Message.objects.filter(
            sender=message['sender'], 
            receiver=membre_connecte, 
            timestamp=message['last_message_time']
        ).first()

        for message in derniers_messages
    ]
    
    return render(request,"messages_tous.html",{'messages_complets': messages_complets})

def andrana(request):
    return render(request,"test.html")


# def mot_de_passe_oublie(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         try:
#             # Rechercher le membre avec cet email
#             membre = Member.objects.get(email=email)
            
#             # Créer un jeton de réinitialisation (hachage basé sur l'email et la date d'inscription)
#             token = hashlib.sha256((membre.email + membre.date_inscrit.isoformat()).encode()).hexdigest()
            
#             # Envoyer un lien par email avec le jeton
#             lien_reinitialisation = f"http://127.0.0.1:8000/reinitialiser-mot-de-passe/{token}/"
#             send_mail(
#                 "Réinitialisation de votre mot de passe",
#                 f"Bonjour {membre.pseudo},\n\nCliquez sur le lien suivant pour réinitialiser votre mot de passe : {lien_reinitialisation}",
#                 "admin@votre_site.com",
#                 [email],
#                 fail_silently=False,
#             )
#             return render(request, "mot_de_passe_envoye.html")
#         except Member.DoesNotExist:
#             return render(request, "mot_de_passe_oublie.html", {"erreur": "Email introuvable."})

#     return render(request, "mot_de_passe_oublie.html")
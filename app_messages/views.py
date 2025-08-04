from django.shortcuts import render, get_object_or_404,redirect
from django.http import JsonResponse
from app_membres.models import Member, Profil
from .models import Message, Photo
from django.db.models import Q
from django.utils.timezone import now, localtime
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import base64
import json
from app_membres.decorators import attente_validation_required
from django.contrib import messages

@attente_validation_required
def aff_message(request, membre_id):
    member = get_object_or_404(Member, id=membre_id)
    user = Member.objects.get(id=request.session["client"]["id"])

    # Vérifier le blocage
    user_has_blocked = member in user.blocked_members.all()
    member_has_blocked = user in member.blocked_members.all()
    blocked = user_has_blocked or member_has_blocked

    if blocked:
        # Rediriger vers la page de profil bloqué (même logique que detail_profil)
        from app_messages.models import Photo  # Correction de l'import
        photo = Photo.objects.filter(membre_nom_id=member.id).order_by('-date').first()
        return render(request, 'profil_bloque.html', {
            'member': member,
            'photo': photo,
            'user_has_blocked': user_has_blocked,
            'user_is_blocked': member_has_blocked,
        })

    if request.method == "POST":
        content = request.POST.get("message", "")
        image = request.FILES.get("image")
        message = Message.objects.create(sender=user, receiver=member, content=content, image=image)
        # Correction : heure locale
        heure_locale = localtime(message.timestamp).strftime('%H:%M')
        return JsonResponse({
            'success': True,
            'message': {
                'content': message.content,
                'image_url': message.image.url if message.image else None,
                'timestamp': heure_locale,
            }
        })

    messages = Message.objects.filter(
        ((Q(sender=user) & Q(receiver=member)) | (Q(sender=member) & Q(receiver=user)))
    ).exclude(deleted_for=user).order_by('timestamp')

    # Marquer les messages comme lus
    for message in messages:
        if message.receiver == user and not message.is_read:
            message.is_read = True
            message.save()

    return render(request, "message_priver.html", {
        "messages": messages,
        "member": member,
        "blocked": False,
        "user_has_blocked": False,
    })

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
    if not request.session.get("client"):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    try:
        user = Member.objects.get(id=request.session["client"]["id"])
        other_member = Member.objects.get(id=membre_id)
        # Marquer tous les messages de la conversation comme supprimés pour l'utilisateur connecté
        messages = Message.objects.filter(
            (Q(sender=user, receiver=other_member) | Q(sender=other_member, receiver=user))
        )
        for msg in messages:
            msg.deleted_for.add(user)
        return JsonResponse({'success': True, 'message': 'Messages supprimés pour vous.'})
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    except Exception as e:
        print(f"Error deleting messages: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)

@csrf_exempt
def delete_all_messages_for_me(request, member_id):
    if request.method == "DELETE":
        user_id = request.session.get('client')
        if not user_id:
            return JsonResponse({"success": False, "error": "Non authentifié"})
        # On marque tous les messages comme supprimés pour cet utilisateur
        messages = Message.objects.filter(
            (Q(sender_id=user_id, receiver_id=member_id) | Q(sender_id=member_id, receiver_id=user_id))
        )
        for msg in messages:
            msg.deleted_for.add(user_id)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Méthode non autorisée"})

# def messages_tous(request):
#     membre_connecte = request.session["client"]["id"]  
#     derniers_messages = (
#         Message.objects.filter(receiver=membre_connecte) 
#         .values('sender')  
#         .annotate(last_message_time=Max('timestamp'))  
#         .order_by('-last_message_time')  
#     )

    
#     messages_complets = [
#         Message.objects.filter(
#             sender=message['sender'], 
#             receiver=membre_connecte, 
#             timestamp=message['last_message_time']
#         ).first()

#         for message in derniers_messages
#     ]
    
#     Message.objects.filter(receiver_id=membre_connecte, is_read=False).update(is_read=True)

    
#     # Remettre le compteur à zéro après affichage
#     if "client" in request.session:
#         request.session["client"]["messages_count"] = 0

#     return render(request, "messages_tous.html", {'messages_complets': messages_complets})

@attente_validation_required
def messages_tous(request):
    membre_connecte = request.session["client"]["id"]
    user = Member.objects.get(id=membre_connecte)
    # Récupérer le profil du membre connecté
    photo_valider = Profil.objects.filter(membre=user).first()

    # Récupérer le dernier message reçu de chaque expéditeur
    derniers_messages = (
        Message.objects.filter(receiver=user)
        .exclude(deleted_for=user)
        .values('sender')
        .annotate(last_message_time=Max('timestamp'))
        .order_by('-last_message_time')
    )

    messages_complets = [
        Message.objects.filter(
            sender_id=msg['sender'],
            receiver=user,
            timestamp=msg['last_message_time']
        ).first()
        for msg in derniers_messages
    ]

    # Marquer comme lus les messages reçus non lus
    Message.objects.filter(receiver=user, is_read=False).update(is_read=True)

    # Remettre le compteur à zéro après affichage
    if "client" in request.session:
        request.session["client"]["messages_count"] = 0

    return render(request, "messages_tous.html", {
        'messages_complets': messages_complets,
        'photo_valider': photo_valider
    })

def envoyer_photo(request, membre_id):
    if request.method == 'POST':
        from .models import Photo
        # Empêcher l'envoi si une photo existe déjà
        if Photo.objects.filter(membre_nom_id=membre_id).exists():
            client_id = request.session.get("client", {}).get("id")
            messages.error(request, "Vous avez déjà envoyé une photo. Veuillez attendre la validation ou contacter l'administrateur.")
            return redirect("mon_profil", membre_id=client_id)
        user = Member.objects.get(id=membre_id)
        
        photo_data = request.POST.get('photo')
        if not photo_data or ';base64,' not in photo_data:
            return render(request, "validation_photo.html", {
                'error': "Format de photo invalide ou photo manquante. Veuillez réessayer."
            })
        try:
            format, imgstr = photo_data.split(';base64,')
            ext = format.split('/')[-1]
            photo = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        except Exception:
            return render(request, "validation_photo.html", {
                'error': "Erreur lors du traitement de la photo. Veuillez réessayer."
            })

        membre = Member.objects.get(id=membre_id)
        Photo.objects.create(membre_nom=membre, images=photo)
        # Message de succès et redirection vers son propre profil
        client_id = request.session.get("client", {}).get("id")
        messages.success(request, "Votre photo a été envoyée à l'espace admin. Si elle n'est pas validée rapidement, veuillez contacter l'administrateur.")
        return redirect("mon_profil", membre_id=client_id)
    return render(request, "detail_profil.html", {"erreur": "Veuillez prendre une photo pour accéder aux messages privés."})

# @csrf_exempt
# def get_received_messages(request, membre_id):
#     if request.method == 'GET':
#         try:
#             user = Member.objects.get(id=request.session["client"]["id"])
#             member = get_object_or_404(Member, id=membre_id)

#             # Fetch messages between the two users
#             messages = Message.objects.filter(
#                 (Q(sender=user) & Q(receiver=member)) | (Q(sender=member) & Q(receiver=user))
#             ).order_by('timestamp')

#             # Prepare the messages data
#             messages_data = [
#                 {
#                     'id': message.id,
#                     'content': message.content,
#                     'image_url': message.image.url if message.image else None,
#                     'timestamp': message.timestamp.strftime('%H:%M'),
#                     'sender_id': message.sender.id,
#                 }
#                 for message in messages
#             ]

#             return JsonResponse({'success': True, 'messages': messages_data})
#         except Exception as e:
#             print(f"Error: {e}")
#             return JsonResponse({'success': False, 'error': 'Internal Server Error'}, status=500)
#     return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def get_received_messages(request, membre_id):
    if request.method == 'GET':
        try:
            user = Member.objects.get(id=request.session["client"]["id"])
            member = get_object_or_404(Member, id=membre_id)

            # Exclure les messages supprimés pour l'utilisateur connecté
            messages = Message.objects.filter(
                (Q(sender=user) & Q(receiver=member)) | (Q(sender=member) & Q(receiver=user))
            ).exclude(deleted_for=user).order_by('timestamp')

            messages_data = [
                {
                    'id': message.id,
                    'content': message.content,
                    'image_url': message.image.url if message.image else None,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                    'sender_id': message.sender.id,
                }
                for message in messages
            ]

            return JsonResponse({'success': True, 'messages': messages_data})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'success': False, 'error': 'Internal Server Error'}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def send_message(request, membre_id):
    if request.method == 'POST':
        try:
            user = Member.objects.get(id=request.session["client"]["id"])
            member = get_object_or_404(Member, id=membre_id)
            content = request.POST.get("message", "")
            image = request.FILES.get("image")

            message = Message.objects.create(sender=user, receiver=member, content=content, image=image)

            # Notifier le destinataire via WebSocket
            channel_layer = get_channel_layer()
            messages_count = Message.objects.filter(
                receiver=member,
                is_read=False
            ).exclude(deleted_for=member).count()
            async_to_sync(channel_layer.group_send)(
                f"user_{member.id}",
                {
                    'type': 'new_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'image_url': message.image.url if message.image else None,
                        'timestamp': message.timestamp.strftime('%H:%M'),
                        'sender_id': message.sender.id,
                    },
                    'count': messages_count,
                }
            )

            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'image_url': message.image.url if message.image else None,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                    'sender_id': message.sender.id,
                }
            })
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'success': False, 'error': 'Internal Server Error'}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def messages_unread_count(request):
    if not request.session.get("client"):
        return JsonResponse({'count': 0})
    user_id = request.session["client"]["id"]
    count = Message.objects.filter(
        receiver_id=user_id,
        is_read=False
    ).exclude(deleted_for__id=user_id).count()
    return JsonResponse({'count': count})

@csrf_exempt
def delete_selected_messages(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            message_ids = data.get('ids', [])
            
            # Vérifier que l'utilisateur a le droit de supprimer ces messages
            user_id = request.session.get("client", {}).get("id")
            if not user_id:
                return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=401)
                
            # Supprimer les messages qui appartiennent à l'utilisateur
            Message.objects.filter(id__in=message_ids).filter(
                Q(sender_id=user_id) | Q(receiver_id=user_id)
            ).delete()
            
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Données invalides'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

def validation_photo(request):
    membre_id = request.session.get("client", {}).get("id")
    membre = None
    if membre_id:
        from app_membres.models import Member
        membre = Member.objects.filter(id=membre_id).first()
        from .models import Photo
        # Vérifier si une photo existe déjà pour ce membre
        if Photo.objects.filter(membre_nom_id=membre_id).exists():
            # Rediriger vers son profil si une photo existe déjà
            return redirect("mon_profil", membre_id=membre_id)
    return render(request, "validation_photo.html", {"membre": membre})




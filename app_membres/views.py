from django.views.decorators.csrf import csrf_exempt
# --- Upload AJAX de la photo de profil ---
from django.views.decorators.http import require_POST
from django.conf import settings
import os
from App_activation_inscription.models import Activation_btn
@csrf_exempt
@require_POST
def upload_profile_image(request):
    user_id = request.session.get('client', {}).get('id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Non authentifié'})
    try:
        member = Member.objects.get(id=user_id)
        profil = Profil.objects.get(membre=member)
    except (Member.DoesNotExist, Profil.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Profil introuvable'})
    image = request.FILES.get('profile_img')
    if not image:
        return JsonResponse({'success': False, 'error': 'Aucune image'})
    # Supprimer l'ancienne image si besoin (optionnel)
    if profil.images and hasattr(profil.images, 'path') and os.path.isfile(profil.images.path):
        try:
            os.remove(profil.images.path)
        except Exception:
            pass
    profil.images = image
    profil.save()
    # Mettre à jour la session
    request.session['client']['profil_image'] = profil.images.url
    request.session.modified = True
    return JsonResponse({'success': True, 'image_url': profil.images.url})
from django.views.decorators.http import require_POST
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from .models import Member, Profil, Like, Dislike, Heart, AdditionalProfileInfo, Notification, Friendship, Follower, ProfileVisit
import re, hashlib
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.db import connection, transaction
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, F, ExpressionWrapper, IntegerField
from django.db.models.functions import Now, ExtractYear
from datetime import date, timedelta
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password  # Pour vérifier les mots de passe
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from app_messages.models import Photo, Message
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from datetime import datetime
import json
from .decorators import membre_validation_required, condition_required, attente_validation_required


def aff_register(request):
    if request.session.get("client"):
        return redirect('membres') 
    return render(request, "register.html")

# Remove @condition_required from aff_login to prevent infinite redirect
def aff_login(request):
    if request.session.get("client"):
        return redirect('membres')  # Redirection vers la page membre
    return render(request, "login.html")

def mdp_crypter(mdp):
    mdp_hasher = hashlib.sha384()
    mdp_hasher.update(mdp.encode("utf-8"))
    return mdp_hasher.hexdigest()

def enregistrer_membres(request):
    if request.method == "POST":
        pseudo = request.POST.get("pseudo")
        email = request.POST.get("email")
        birthday = request.POST.get("birthdate")
        country = request.POST.get("country")
        city = request.POST.get("city")
        genre = request.POST.get("gender")
        genre_chercher = request.POST.get("looking_for")
        password = request.POST.get("password")
        password_confirm = request.POST.get("confirm_password")
        terms_accepted = request.POST.get("terms") == "on"
        age_confirmer = request.POST.get("age") == "on"
        age_debut = request.POST.get('age_debut')
        age_fin = request.POST.get('age_fin')

        if all([pseudo, email, birthday, country, city, genre, genre_chercher, password]):
            # Vérifier si le pseudo existe déjà
            if User.objects.filter(username__iexact=pseudo).exists():
                return render(request, 'register.html', {
                    'message': "Ce pseudo est déjà utilisé. Veuillez en choisir un autre.",
                    'error_field': 'pseudo'
                })

            # Vérifier si l'email existe déjà
            if Member.objects.filter(email=email).exists():
                return render(request, 'register.html', {
                    'message': "Cette adresse email est déjà utilisée.",
                    'error_field': 'email'
                })

            # Vérifier les mots de passe
            if password != password_confirm:
                return render(request, 'register.html', {
                    'message': "Les mots de passe ne correspondent pas.",
                    'error_field': 'password'
                })

            if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
                return render(request, 'register.html', {
                    'message': "Le mot de passe doit contenir au moins 8 caractères, des lettres et des chiffres.",
                    'error_field': 'password'
                })

            try:
                with transaction.atomic():
                    # Créer l'utilisateur
                    user = User.objects.create_user(
                        username=pseudo,
                        email=email,
                        password=password
                    )
                    # Créer le membre
                    member = Member.objects.create(
                        user=user,
                        pseudo=pseudo,
                        email=email,
                        birthdate=birthday,
                        country=country,
                        city=city,
                        gender=genre,
                        looking_for=genre_chercher,
                        password=mdp_crypter(password),
                        terms_accepted=terms_accepted,
                        age_confirmed=age_confirmer,
                        is_active=True,
                        email_confirmed=True,
                        age_debut=age_debut,
                        age_fin=age_fin
                    )

                    profil = Profil.objects.filter(membre=member).first()
                    profil_image = profil.images.url if profil and profil.images else None

                    # Mettre à jour la session
                    request.session["client"] = {
                        "id": member.id,
                        "pseudo": member.pseudo,
                        "email": member.email,
                        "gender": member.gender,
                        "country": member.country,
                        "date_inscrit": str(member.date_inscrit),
                        "likes_count": member.likes_received_count,
                        "notifications_count": member.notifications_count,
                        "hearts_count": member.hearts_received_count,
                        "profil_image": str(profil_image),
                    }
                    return redirect("condition")
            except Exception as e:
                import traceback
                print(f"Erreur lors de l'inscription : {str(e)}\n{traceback.format_exc()}")
                return render(request, 'register.html', {
                    'message': f"Une erreur est survenue lors de l'inscription : {str(e)}",
                    'error_field': 'general'
                })
        else:
            return render(request, 'register.html', {
                'message': "Veuillez remplir tous les champs obligatoires.",
                'error_field': 'general'
            })
    return redirect("aff_register")

@never_cache
def connexion_membre(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return render(request, "login.html", {"message": "Utilisateur non inscrit."})
            try:
                member = Member.objects.get(user=user)
            except Member.DoesNotExist:
                return render(request, "login.html", {"message": "Aucun compte membre lié à cet utilisateur."})
            if user.check_password(password):
                profil = Profil.objects.filter(membre=member).first()
                profil_image = profil.images.url if profil and profil.images else None
                messages_count = Message.objects.filter(
                    receiver=member,
                    is_read=False
                ).exclude(deleted_for=member).count()
                request.session["client"] = {
                    "id": member.id,
                    "pseudo": member.pseudo,
                    "email": member.email,
                    "gender": member.gender,
                    "country": member.country,
                    "date_inscrit": str(member.date_inscrit),
                    "likes_count": member.likes_received_count,
                    "notifications_count": member.notifications_count,
                    "hearts_count": member.hearts_received_count,
                    "profil_image": str(profil_image),
                    "messages_count": messages_count,
                }
                if member.desactivation == True:
                    return redirect("activer_compte")
                # On ne redirige plus ici si desactivation == False, on laisse la suite s'exécuter
                member.is_active = True
                member.save(update_fields=['is_active'])
                activation = Activation_btn.objects.first()
                if profil and profil.valider or activation.status.lower() == 'inactif':
                    return redirect("membres")
                elif profil or activation.status.lower() == 'actif': 
                    return redirect("Attente_validation")
                else:
                    return HttpResponseRedirect(f"/condition_admi/?id={member.id}")
            else:
                return render(request, "login.html", {"message": "Email ou mot de passe incorrect."})
        else:
            return render(request, "login.html", {"message": "Tous les champs doivent être remplis."})
    return render(request, "login.html")

def Entrer_image(request,image):
    if "images" in request.FILES:
        fichiers = request.FILES["images"]
        path = os.path.splitext(fichiers.name)
        
        new_name = f"{image}{path[1]}"
        emplacement = os.path.join(f"{settings.STORAGE_IMAGE}/profils/",new_name)
        with open(emplacement, "wb") as destination:
            for donner in fichiers.chunks():
                destination.write(donner)

        return new_name
    


def condition_admi(request):
    if not request.session.get("client"):
        return redirect('aff_login')
    membre_id = request.session.get("client", {}).get("id")
    from app_membres.models import Profil
    profil = Profil.objects.filter(membre_id=membre_id).first() if membre_id else None
    # Si une image existe déjà dans le profil, ne pas retourner dans condition_admi
    if profil and profil.images:
        return redirect('membres')
    profil_exists = bool(profil)
    if not profil_exists:
        if request.path != '/condition_admi/':
            return redirect('condition_admi')
    if request.method == "POST":
        membre_id = request.session.get("client", {}).get("id")
        cheuveux = request.POST.get('cheveux')
        yeux =request.POST.get('yeux')
        taille =request.POST.get('taille')
        poids = request.POST.get('poids')
        alcool = request.POST.get('alcool')
        tabac = request.POST.get('tabac')
        situation = request.POST.get('situation')
        description =request.POST.get('description')
        recherche = request.POST.get('recherche')
        
        if not membre_id:
            return redirect('aff_login')
        membre = Member.objects.get(id=membre_id)
        pseudo = request.session["client"].get("pseudo")
        # Correction: vérifier si un profil existe déjà pour ce membre
        if not Profil.objects.filter(membre=membre).exists():
            if poids and alcool and taille and tabac and description and recherche:
                profil = Profil.objects.create(
                    membre=membre,
                    sexe=membre.gender,
                    cheveux=cheuveux,
                    yeux=yeux,
                    taille=int(taille),
                    poids= int(poids),
                    alcool= alcool,
                    tabac= tabac,
                    situation= situation,
                    enfants=int(request.POST.get('enfants')) if request.POST.get('enfants') and request.POST.get('enfants').isdigit() else 0,
                    description= description,
                    recherche=recherche,
                    images=f"{settings.STORAGE_IMAGE}/profils/{Entrer_image(request,pseudo)}"
                )
                
                request.session["client"] = {
                    "id": membre.id,
                    "pseudo": membre.pseudo,
                    "email": membre.email,
                    "gender": membre.gender,
                    "country": membre.country,
                    "date_inscrit": str(membre.date_inscrit),
                    "likes_count": membre.likes_received_count,
                    "notifications_count": membre.notifications_count,
                    "hearts_count": membre.hearts_received_count,
                    "profil_image": str(f"{profil.images}"),
                }
            else:
                return render(request, "condition.html", {"messages": "Veuillez remplir tous les champs"})

            # Le profil est automatiquement validé si c'est un homme 
            # ou si la validation automatique est activée
            if profil.valider:
                return redirect('membres')
            else:
                return redirect("Attente_validation")
        else:
            return render(request, "condition.html", {"messages": "Votre Profil est deja exister"})

    return render(request, 'condition.html')

@condition_required
@attente_validation_required
def membre_inscrit(request):
    if not request.session.get("client"):
        return redirect('aff_login')
    # Si déjà connecté et sur la page membres, bloquer l'accès direct à attente_validation

    membre_id = request.session.get("client", {}).get("id")
    if not membre_id:
        return redirect('aff_login')
    membre = Member.objects.get(id=membre_id)
    profil = Profil.objects.filter(membre=membre).first()
    additional_info, _ = AdditionalProfileInfo.objects.get_or_create(membre=membre)

    # Vérification de l'acceptation des conditions d'utilisation
    if not membre.terms_accepted:
        return redirect('condition_util')

    # Filtres GET
    country_filter = request.GET.get('country', '').strip()
    age_min = request.GET.get('age_min')
    age_max = request.GET.get('age_max')


    sexe_recherche = "Homme" if membre.gender == "Femme" else "Femme"
    membres_qs = Member.objects.filter(gender=sexe_recherche)


    from App_activation_inscription.models import Activation_btn


    # Filtrer les membres bloqués
    blocked_ids = membre.blocked_members.values_list('id', flat=True)
    membres_qs = membres_qs.exclude(id__in=blocked_ids)

    membres_qs = membres_qs.annotate(
        age=ExpressionWrapper(
            ExtractYear(Now()) - ExtractYear(F('birthdate')),
            output_field=IntegerField()
        )
    )

    if country_filter:
        membres_qs = membres_qs.filter(country__iexact=country_filter)

    # Filtre âge
    if age_min:
        membres_qs = membres_qs.filter(age__gte=int(age_min))
    if age_max:
        membres_qs = membres_qs.filter(age__lte=int(age_max))

    profil_booster = membres_qs.order_by('-likes_received')[:4]
    membres_reste = membres_qs.exclude(id__in=[m.id for m in profil_booster])

    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(membres_reste, 50)  # 50 membres par page
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    for membre in profil_booster:
        membre.age_debut = getattr(membre, 'age_debut', None)
        membre.age_fin = getattr(membre, 'age_fin', None)
    for membre in page_obj:
        membre.age_debut = getattr(membre, 'age_debut', None)
        membre.age_fin = getattr(membre, 'age_fin', None)

    context = {
        'profil': profil,
        'membre': membre,
        "membres_tous": page_obj,  # paginé
        "membres_donner": profil_booster,
        "likes_count": membre.likes_received_count,
        "notifications_count": membre.notifications_count,
        "hearts_count": membre.hearts_received_count,
        'page_obj': page_obj,
    }
    # print(page_obj.profile)
    return render(request, 'membres.html', context)

@attente_validation_required
@attente_validation_required
def like_member(request, member_id):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    liker_id = request.session.get("client", {}).get("id")
    if not liker_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    liker = Member.objects.get(id=liker_id)
    liked = get_object_or_404(Member, id=member_id)
    if liker != liked:
        like, created = Like.objects.get_or_create(liker=liker, liked=liked)
        if not created:
            like.delete()
        else:
            Notification.objects.create(
                recipient=liked,
                sender=liker,
                message=f"{liker.pseudo} a aimé votre profil.",
                url=f"/profile/{liker.id}/"
            )
    return JsonResponse({'likes_count': liked.likes_received_count})

@attente_validation_required
@attente_validation_required
def fetch_notifications(request):
    user_id = request.session.get("client", {}).get("id")
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    member = Member.objects.get(id=user_id)
    notifications = Notification.objects.filter(recipient=member, is_read=False).order_by('-timestamp')
    data = [
        {"message": n.message, "url": n.url, "timestamp": n.timestamp.strftime('%Y-%m-%d %H:%M')}
        for n in notifications
    ]
    return JsonResponse({'notifications': data})

@csrf_exempt
def mark_notifications_as_read(request):
    user_id = request.session.get("client", {}).get("id")
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    member = Member.objects.get(id=user_id)
    Notification.objects.filter(recipient=member, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})



def Attente_validation(request):
    membre_id = request.session.get("client", {}).get("id")
    referer = request.META.get('HTTP_REFERER', '')

    # Récupération du profil si membre connecté
    profil = Profil.objects.filter(membre_id=membre_id).first() if membre_id else None

    # Récupération du bouton d'activation
    activation = Activation_btn.objects.first()
    print(activation.status)

    if activation and activation.status.lower() == 'actif':
        if profil and profil.valider and (
            'membres' in referer or request.path == '/attente_validation/'
        ):
            return redirect('membres')

        if not membre_id:
            return redirect('aff_login')

        profil_exists = Profil.objects.filter(membre_id=membre_id).exists()
        if not profil_exists:
            return redirect('condition_admi')

        return render(request, "attente_validation.html")
    
    # Si le bouton d'activation n'existe pas ou est inactif
    else:
        return redirect('membres')


def condition(request):
    return redirect("condition_admi")

@attente_validation_required
def dislike_member(request, member_id):
    disliker_id = request.session.get("client", {}).get("id")
    if not disliker_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    disliker = Member.objects.get(id=disliker_id)
    disliked = get_object_or_404(Member, id=member_id)
    if disliker != disliked:
        dislike, created = Dislike.objects.get_or_create(disliker=disliker, disliked=disliked)
        if not created:
            dislike.delete()
    return JsonResponse({'success': True})

def deconnexion(request):
    request.session.clear()
    logout(request)
    return redirect("aff_login")

@attente_validation_required
def heart_member(request, member_id):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    giver_id = request.session.get("client", {}).get("id")
    if not giver_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    giver = Member.objects.get(id=giver_id)
    receiver = get_object_or_404(Member, id=member_id)
    if giver != receiver:
        heart, created = Heart.objects.get_or_create(giver=giver, receiver=receiver)
        if not created:
            heart.delete()
        else:
            Notification.objects.create(
                recipient=receiver,
                sender=giver,
                message=f"{giver.pseudo} vous a envoyé un cœur.",
                url=f"/profile/{giver.id}/"
            )
    return JsonResponse({'hearts_count': receiver.hearts_received_count})

@attente_validation_required
def ajout_additional(request):
    if request.method == "POST":
        membre_id = request.session.get("client", {}).get("id")
        if not membre_id:
            return redirect('aff_login')
        membre = Member.objects.get(id=membre_id)
        nom = request.session["client"].get("pseudo")
        additional_info, _ = AdditionalProfileInfo.objects.get_or_create(membre=membre)

        # Mise à jour des champs
        additional_info.ethnicite = request.POST.get('ethnicite', additional_info.ethnicite)
        additional_info.art_corporel = request.POST.get('art_corporel', additional_info.art_corporel)
        additional_info.enfants_souhaites = request.POST.get('enfants_souhaites', additional_info.enfants_souhaites)
        additional_info.profession = request.POST.get('profession', additional_info.profession)
        additional_info.situation_vie = request.POST.get('situation_vie', additional_info.situation_vie)
        additional_info.demenagement = request.POST.get('demenagement', additional_info.demenagement)
        additional_info.relation_recherche = request.POST.get('relation_recherche', additional_info.relation_recherche)
        additional_info.niveau_etude = request.POST.get('niveau_etude', additional_info.niveau_etude)
        additional_info.religion = request.POST.get('religion', additional_info.religion)
        additional_info.signe_astrologique = request.POST.get('signe_astrologique', additional_info.signe_astrologique)

       
        upload_to = os.path.join(settings.STORAGE_IMAGE, '/membres')

        if not os.path.exists(upload_to):
            os.makedirs(upload_to)

        for i in range(1, 7):
            image_field = f'additional_image{i}' 
            

            if image_field in request.FILES:
                uploaded_image = request.FILES[image_field]
                
                  

                file_extension = uploaded_image.name.split('.')[-1]  
                new_filename = f"{nom}_{i}.{file_extension}" 

                new_image_path = os.path.join(settings.STORAGE_IMAGE,'/membres', new_filename)
                

                fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, settings.STORAGE_IMAGE))
                
                saved_file = fs.save(new_image_path, uploaded_image)

                setattr(additional_info, image_field, os.path.join('static', saved_file))




        additional_info.save()
        return redirect('mon_profil', membre_id=membre.id)
    return render(request, 'condition.html')

@attente_validation_required
@attente_validation_required
def modifier_profil(request):
    if not request.session.get("client"):
        return redirect('aff_login')
    membre_id = request.session.get("client", {}).get("id")
    if not membre_id:
        return redirect('aff_login')
    membre = Member.objects.get(id=membre_id)
    profil = Profil.objects.get(membre=membre)

    if request.method == "POST":
        membre.pseudo = request.POST.get('pseudo', membre.pseudo)
        membre.email = request.POST.get('email', membre.email)
        membre.country = request.POST.get('country', membre.country)
        membre.city = request.POST.get('city', membre.city)
        membre.gender = request.POST.get('gender', membre.gender)
        membre.looking_for = request.POST.get('looking_for', membre.looking_for)
        membre.age_debut = request.POST.get('age_debut',membre.age_debut)
        membre.age_fin = request.POST.get('age_fin',membre.age_fin)
        membre.save()

        profil.cheveux = request.POST.get('cheveux', profil.cheveux)
        profil.yeux = request.POST.get('yeux', profil.yeux)
        profil.taille = int(request.POST.get('taille', profil.taille))
        profil.poids = int(request.POST.get('poids', profil.poids))
        profil.description = request.POST.get('description', profil.description)
        profil.recherche = request.POST.get('recherche', profil.recherche)
        if 'images' in request.FILES:
            profil.images = request.FILES['images']
        profil.save()

        # Update AdditionalProfileInfo fields
        from .models import AdditionalProfileInfo
        additional_info, _ = AdditionalProfileInfo.objects.get_or_create(membre=membre)
        additional_info.ethnicite = request.POST.get('ethnicite', additional_info.ethnicite)
        additional_info.art_corporel = request.POST.get('art_corporel', additional_info.art_corporel)
        additional_info.enfants_souhaites = request.POST.get('enfants_souhaites', additional_info.enfants_souhaites)
        additional_info.profession = request.POST.get('profession', additional_info.profession)
        additional_info.situation_vie = request.POST.get('situation_vie', additional_info.situation_vie)
        additional_info.demenagement = request.POST.get('demenagement', additional_info.demenagement)
        additional_info.relation_recherche = request.POST.get('relation_recherche', additional_info.relation_recherche)
        additional_info.niveau_etude = request.POST.get('niveau_etude', additional_info.niveau_etude)
        additional_info.religion = request.POST.get('religion', additional_info.religion)
        additional_info.signe_astrologique = request.POST.get('signe_astrologique', additional_info.signe_astrologique)

        # Handle additional images if present
        for i in range(1, 7):
            image_field = f'additional_image{i}'
            if image_field in request.FILES:
                additional_info.__setattr__(image_field, request.FILES[image_field])
        additional_info.save()

        return redirect('mon_profil', membre_id=membre.id)

    # Ajout de la validation pour photo_valider
    photo_valider = None
    if hasattr(profil, 'valider'):
        photo_valider = profil
    context = {
        'profil': profil,
        'membre': membre,
        'age': membre.caluler_age() if hasattr(membre, 'caluler_age') and membre.birthdate else None,
        'photo_valider': photo_valider
    }
    return render(request, 'mon_profil.html', context)


@attente_validation_required
def aff_parametres(request, id_membre):
    if not request.session.get("client"):
        return redirect("aff_login")
    membre = get_object_or_404(Member, id=id_membre)
    context = {
        "membre": membre,
        "id_membre": id_membre  
    }
    return render(request, "parametres.html", context)


def supprimer_membre_par_id(request, id_membre):
    client_id = request.session.get("client", {}).get("id")
    if not client_id:
        return redirect("aff_login")
    membre = get_object_or_404(Member, id=id_membre)
    if str(id_membre) != str(request.session["client"]["id"]):
        messages.error(request, "Vous ne pouvez supprimer que votre propre compte.")
        return redirect("parametres", id_membre=id_membre)

    if request.method == "POST":
        password = request.POST.get("password")
        
        if not check_password(password, membre.user.password):
            messages.error(request, "Mot de passe incorrect.")
            return redirect("parametres", id_membre=id_membre)

        try:
            with transaction.atomic():
                # 1. Supprimer d'abord les relations many-to-many et one-to-many
                Notification.objects.filter(Q(sender=membre) | Q(recipient=membre)).delete()
                Message.objects.filter(Q(sender=membre) | Q(receiver=membre)).delete()
                Photo.objects.filter(membre_nom=membre).delete()
                Like.objects.filter(Q(liker=membre) | Q(liked=membre)).delete()
                Dislike.objects.filter(Q(disliker=membre) | Q(disliked=membre)).delete()
                Heart.objects.filter(Q(giver=membre) | Q(receiver=membre)).delete()
                Friendship.objects.filter(Q(sender=membre) | Q(receiver=membre)).delete()
                Follower.objects.filter(Q(follower=membre) | Q(followed=membre)).delete()

                # 2. Supprimer les relations one-to-one
                try:
                    if hasattr(membre, 'profil'):
                        membre.profil.delete()
                except Profil.DoesNotExist:
                    pass

                try:
                    if hasattr(membre, 'additionalprofileinfo'):
                        membre.additionalprofileinfo.delete()
                except AdditionalProfileInfo.DoesNotExist:
                    pass

                # 3. Récupérer l'utilisateur avant de supprimer le membre
                user = membre.user

                # 4. Supprimer le membre
                membre.delete()

                # 5. Supprimer l'utilisateur Django
                if user:
                    user.delete()

                messages.success(request, "Votre compte a été supprimé avec succès.")
                request.session.flush()
                
                return redirect("aff_login")
                
        except Exception as e:
            print(f"Error deleting member: {str(e)}")
            messages.error(request, "Une erreur s'est produite lors de la suppression. Veuillez réessayer.")
            return redirect("parametres", id_membre=id_membre)

    return redirect("parametres", id_membre=id_membre)

def send_friend_request(request, member_id):
    sender_id = request.session.get("client", {}).get("id")
    if not sender_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    sender = Member.objects.get(id=sender_id)
    receiver = get_object_or_404(Member, id=member_id)

    if sender != receiver:
        friendship, created = Friendship.objects.get_or_create(sender=sender, receiver=receiver)
        if not created:
            return JsonResponse({'error': 'Friend request already sent'}, status=400)
        return JsonResponse({'success': True, 'message': 'Friend request sent successfully'})
    return JsonResponse({'error': 'Cannot send friend request to yourself'}, status=400)

def accept_friend_request(request, friendship_id):
    receiver_id = request.session.get("client", {}).get("id")
    if not receiver_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    friendship = get_object_or_404(Friendship, id=friendship_id, receiver_id=receiver_id)
    friendship.is_accepted = True
    friendship.save()
    return JsonResponse({'success': True, 'message': 'Friend request accepted'})

def list_friends(request):
    member_id = request.session.get("client", {}).get("id")
    if not member_id:
        return redirect('aff_login')
    member = Member.objects.get(id=member_id)
    friends = Member.objects.filter(
        Q(friend_requests_sent__receiver=member, friend_requests_sent__is_accepted=True) |
        Q(friend_requests_received__sender=member, friend_requests_received__is_accepted=True)
    )
    return render(request, "friends_list.html", {"friends": friends})

def follow_member(request, member_id):
    if request.method == "POST" and request.session.get("client"):
        follower_id = request.session.get("client", {}).get("id")
        if not follower_id:
            return JsonResponse({'success': False, 'message': 'Invalid session'}, status=400)
        follower = Member.objects.get(id=follower_id)
        followed = get_object_or_404(Member, id=member_id)
        existing_follow = Follower.objects.filter(follower=follower, followed=followed).first()

        if existing_follow:
            existing_follow.delete()
            return JsonResponse({'success': True, 'message': 'Unfollowed successfully', 'is_following': False})
        else:
            Follower.objects.create(follower=follower, followed=followed)
            return JsonResponse({'success': True, 'message': 'Followed successfully', 'is_following': True})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def list_followers(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    followers = Follower.get_followers(member)
    return render(request, "followers_list.html", {"followers": followers})

def changer_mot_de_passe(request, id_membre):
    client_id = request.session.get("client", {}).get("id")
    if not client_id:
        return redirect("aff_login")
    membre = get_object_or_404(Member, id=id_membre)
    if str(id_membre) != str(client_id):
        messages.error(request, "Vous ne pouvez modifier que votre propre mot de passe.")
        return redirect("parametres", id_membre=id_membre)

    if request.method == "POST":
        ancien_mdp = request.POST.get("ancien_mdp")
        nouveau_mdp = request.POST.get("nouveau_mdp")
        confirmer_mdp = request.POST.get("confirmer_mdp")

        if not check_password(ancien_mdp, membre.user.password):
            messages.error(request, "L'ancien mot de passe est incorrect.")
            return redirect("changer_mot_de_passe", id_membre=id_membre)

        if nouveau_mdp != confirmer_mdp:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            return redirect("changer_mot_de_passe", id_membre=id_membre)

        if len(nouveau_mdp) < 8:
            messages.error(request, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
            return redirect("changer_mot_de_passe", id_membre=id_membre)

        try:
            membre.user.set_password(nouveau_mdp)
            membre.user.save()
            membre.password = mdp_crypter(nouveau_mdp)
            membre.save()
            messages.success(request, "Votre mot de passe a été modifié avec succès. Veuillez vous déconnecter puis vous reconnecter pour que la modification soit prise en compte.")
            return redirect("parametres",id_membre=id_membre)
        except Exception as e:
            messages.error(request, "Une erreur s'est produite lors du changement de mot de passe.")
            return redirect("changer_mot_de_passe", id_membre=id_membre)

    return render(request, "changer_mot_de_passe.html", {"membre": membre})

def online_members(request):
    client_id = request.session.get("client", {}).get("id")
    if not client_id:
        return redirect('aff_login')
    # Récupérer tous les membres en ligne
    online_members = Member.objects.filter(
        activiter_dernier__gte=now() - timedelta(minutes=5)
    ).exclude(id=request.session["client"]["id"])

    context = {
        'online_members': online_members,
    }
    return render(request, 'online_members.html', context)

def list_visitors(request, member_id):
    client_id = request.session.get("client", {}).get("id")
    if not client_id:
        return redirect('aff_login')
    if str(member_id) != str(client_id):
        return redirect('membres')
    membre = get_object_or_404(Member, id=member_id)
    visitors = ProfileVisit.objects.filter(visited=membre).select_related('visitor')

    context = {
        'membre': membre,
        'visitors': visitors,
    }
    return render(request, 'visitors_list.html', context)

def mot_de_passe_oublie(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            membre = Member.objects.get(email=email)
            # Générer un token unique
            token = get_random_string(length=32)
            membre.reset_token = token
            membre.reset_token_created = datetime.now()
            membre.save()
            
            # Construire le lien de réinitialisation
            reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{token}/"
            
            # Envoyer l'email
            send_mail(
                'Réinitialisation de votre mot de passe',
                f'Cliquez sur ce lien pour réinitialiser votre mot de passe : {reset_link}\n\nCe lien expirera dans 1 heure.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, "Un email de réinitialisation a été envoyé à votre adresse email.")
            return redirect('mot_de_passe_oublie')
        except Member.DoesNotExist:
            messages.error(request, "Aucun compte n'est associé à cette adresse email.")
    return render(request, 'mot_de_passe_oublie.html')

def reset_password(request, token):
    try:
        membre = Member.objects.get(reset_token=token)
        # Vérifier si le token n'a pas expiré (1 heure de validité)
        from django.utils import timezone
        token_age = timezone.now() - membre.reset_token_created
        if token_age.total_seconds() > 3600:  # Token expire après 1 heure
            messages.error(request, "Ce lien de réinitialisation a expiré.")
            return redirect('mot_de_passe_oublie')
            
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password != confirm_password:
                messages.error(request, "Les mots de passe ne correspondent pas.")
            elif len(password) < 8:
                messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            else:
                membre.password = mdp_crypter(password)
                membre.user.set_password(password)
                membre.reset_token = None
                membre.reset_token_created = None
                membre.user.save()
                membre.save()
                
                messages.success(request, "Votre mot de passe a été réinitialisé avec succès. Veuillez vous connecter.")
                return redirect('aff_login')
                
        return render(request, 'reset_password.html')
        
    except Member.DoesNotExist:
        messages.error(request, "Lien de réinitialisation invalide.")
        return redirect('mot_de_passe_oublie')

@csrf_exempt
def supprimer_photo(request):
    if not request.session.get("client"):
        return JsonResponse({"success": False, "error": "Vous devez être connecté."}, status=401)
    if request.method == "POST":
        data = json.loads(request.body)
        field = data.get("field")
        try:
            membre = Member.objects.get(id=request.session["client"]["id"])
            additional_info = AdditionalProfileInfo.objects.get(membre=membre)
            if hasattr(additional_info, field):
                setattr(additional_info, field, None)
                additional_info.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Champ introuvable"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Méthode non autorisée"})

def notifications_page(request):
    client = request.session.get('client', {})
    client_id = client.get('id')
    if not client_id:
        return redirect('aff_login')
    notifications = Notification.objects.filter(recipient_id=client_id).order_by('-timestamp')
    return render(request, "notifications.html", {"notifications": notifications})

def desactiver_membre_par_id(request,id_membre):
    client_id = request.session.get("client", {}).get("id")
    if not client_id:
        return redirect("aff_login")
    membre = get_object_or_404(Member, id=id_membre)
    if request.method == "POST":
        password = request.POST.get("password")
        if str(id_membre) != str(client_id):
            messages.error(request, "Vous ne pouvez pas desactiver que votre propre compte.")
            return redirect("parametres", id_membre=id_membre)
        
        # Vérifier le mot de passe
        if not check_password(password, membre.user.password):
            messages.error(request, "Mot de passe incorrect.")
            return redirect("parametres", id_membre=id_membre)

        try:
            membre.desactivation = True
            membre.save()
            logout(request)
            request.session.clear()
            return redirect("aff_login")
                
        except Exception as e:
            print(f"Error deleting member: {str(e)}")
            messages.error(request, "Une erreur s'est produite lors de la desactivation de votre compte. Veuillez réessayer.")
            return redirect("parametres", id_membre=id_membre)

    return redirect("parametres", id_membre=id_membre)

            
def valider_activation(request,id_user):
    if not request.session.get("client"):
        return redirect("aff_login")
    
    membre = get_object_or_404(Member,id=id_user)
    
    if request.method == "POST":
        password = request.POST.get("password")
        if not check_password(password, membre.user.password):
            messages.error(request, "Mot de passe incorrect.")
            return redirect("activer_compte")
        
        try:
            membre.desactivation = False
            membre.save()
            return redirect("membres")
        
        except Exception as e:
            print(f"Error deleting member: {str(e)}")
            messages.error(request, "Une erreur s'est produite lors de l' activation de votre compte. Veuillez réessayer.")
            return redirect("activer_compte")
        
    return render(request, "activation_compte.html", {"id_user": id_user})
    

@membre_validation_required
def activer_compte(request):
    client_id = request.session.get("client", {}).get("id")
    if not client_id:
        return redirect("aff_login")
    
    membre = Member.objects.get(id=client_id)
    
    if membre.desactivation:
        return render(request, "activation_compte.html", {"id_user": membre.id})
    
    return redirect("membres")

def aff_message(request, membre_id):
    user_id = request.session.get("client", {}).get("id")
    if not user_id:
        return redirect('aff_login')
    member = get_object_or_404(Member, id=membre_id)
    user = Member.objects.get(id=user_id)

    # Vérifier le blocage
    if member in user.blocked_members.all() or user in member.blocked_members.all():
        return render(request, "message_priver.html", {"member": member, "messages": [], "blocked": True})

    # Vérifier la photo et la validation du profil
    profil = Profil.objects.filter(membre=user).first()
    if not profil or not profil.images:
        return render(request, "validation_photo.html", {"message": "Vous devez avoir une photo de profil pour accéder à la messagerie privée."})
    if not profil.valider:
        # Affichage d'un message d'attente explicite
        return render(request, "validation_photo.html", {"message": "Votre photo de profil est en attente de validation. Vous ne pouvez pas accéder à la messagerie privée tant qu'elle n'est pas validée."})

    messages = Message.objects.filter(
        Q(sender=member, receiver=user) | Q(sender=user, receiver=member)
    ).order_by('timestamp')

    # Marquer les messages comme lus
    for message in messages:
        if message.receiver == user and not message.is_read:
            message.is_read = True
            message.save()

    return render(request, "messages.html", {"messages": messages, "member": member})

def send_message(request, membre_id):
    if request.method == "POST":
        membre_expediteur = request.session.get("client", {}).get("id")
        if not membre_expediteur:
            return redirect('aff_login')
        contenu = request.POST.get("message")
        membre_destinataire = membre_id

        if contenu:
            try:
                message = Message.objects.create(
                    sender_id=membre_expediteur,
                    receiver_id=membre_destinataire,
                    content=contenu
                )

                # Ajouter une notification pour le message envoyé
                Notification.objects.create(
                    recipient_id=membre_destinataire,
                    sender_id=membre_expediteur,
                    message="Vous avez reçu un nouveau message.",
                    url=f"/message/{membre_expediteur}/"
                )

                return redirect("aff_message", membre_id=membre_destinataire)
            except Exception as e:
                messages.error(request, "Erreur lors de l'envoi du message.")
                return redirect("aff_message", membre_id=membre_destinataire)

    return redirect("aff_message", membre_id=membre_id)








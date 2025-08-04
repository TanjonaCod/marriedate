from app_membres.decorators import attente_validation_required
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from app_membres.models import Member, Profil, Like, Dislike, Heart, AdditionalProfileInfo, Notification, Follower  # Import nécessaire
import re, hashlib
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.db import connection
from django.contrib.auth.models import User
from app_messages.models import Photo



def afficher_accueil(request):
    if request.session.get("client"):
        return redirect('membres')  # ou 'membres' selon votre logique
    return render(request, "index.html")


@attente_validation_required
def detail_profil(request, member_id):
    if not request.session.get("client"):
        return redirect('aff_login')
    
    membre = Member.objects.get(id=member_id)

    profil = Profil.objects.filter(membre=membre).first()
    additional_info = AdditionalProfileInfo.objects.filter(membre=membre).first()
    photo_valider = Photo.objects.filter(membre_nom_id=request.session["client"]["id"]).order_by('-date').first()
    followers = Follower.objects.filter(followed=membre)
    is_following = Follower.objects.filter(follower_id=request.session["client"]["id"], followed=membre).exists()


    visitor = Member.objects.get(id=request.session["client"]["id"])
    user_has_blocked = membre in visitor.blocked_members.all()
    user_is_blocked = visitor in membre.blocked_members.all()
    if user_has_blocked or user_is_blocked:
        
        photo = Photo.objects.filter(membre_nom_id=membre.id).order_by('-date').first()
        return render(request, 'profil_bloque.html', {
            'member': membre,
            'photo': photo,
            'user_has_blocked': user_has_blocked,
            'user_is_blocked': user_is_blocked,
        })

    if request.session.get("client"):
        visitor = Member.objects.get(id=request.session["client"]["id"])
        if visitor != membre:
            Notification.objects.create(
                recipient=membre,
                sender=visitor,
                message=f"{visitor.pseudo}",
                url=f"/profile/{visitor.id}/"
            )
    
    context = {
        'membre': membre,
        'profile': profil,
        'additional_info': additional_info,
        'photo_valider': photo_valider,  # Include the most recent photo validation status
        'followers': followers,
        'is_following': is_following,
        'user_has_blocked': user_has_blocked,
        'user_is_blocked': user_is_blocked,
    }
    print(membre)
    return render(request, 'detail_profil.html', context)

@attente_validation_required
def mon_profil(request, membre_id):
    if not request.session.get("client"):
        return redirect('aff_login')
        
    if request.session["client"]["id"] != membre_id:
        return redirect('mon_profil', membre_id=request.session["client"]["id"] )
    
    membre = get_object_or_404(Member, id=membre_id)
    profil = Profil.objects.filter(membre=membre).first()  
    additional_info = AdditionalProfileInfo.objects.filter(membre=membre).first()

    context = {
        "membre": membre,
        "profil": profil,
        "additional_info": additional_info,
    }
    return render(request, "mon_profil.html", context)

def create_notification(recipient, sender, message, url=None):
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        message=message,
        url=url
    )


def profil_image(request):
    if request.user.is_authenticated:
        try:
            return {'profile': request.user.profile}
        except:
            return {'profile': None}
    return {'profile': None}

def follow_member(request, member_id):
    if request.method == "POST" and request.session.get("client"):
        follower = Member.objects.get(id=request.session["client"]["id"])
        followed = get_object_or_404(Member, id=member_id)
        existing_follow = Follower.objects.filter(follower=follower, followed=followed).first()

        if existing_follow:
            # Unfollow if already following
            existing_follow.delete()
            return JsonResponse({'success': True, 'message': 'You have unfollowed this member.', 'is_following': False})
        else:
            # Follow if not already following
            Follower.objects.create(follower=follower, followed=followed)
            return JsonResponse({'success': True, 'message': 'You are now following this member.', 'is_following': True})
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

def list_followers(request, member_id):
    if not request.session.get("client"):
        return redirect('aff_login')
    
    # Vérifiez si l'utilisateur connecté correspond à l'utilisateur dont les abonnés sont affichés
    if request.session["client"]["id"] != member_id:
        return redirect('aff_accueil')

    membre = get_object_or_404(Member, id=member_id)
    followers = Follower.objects.filter(followed=membre)

    context = {
        'membre': membre,
        'followers': followers,
    }
    return render(request, 'followers_list.html', context)


def afficher_propos(request):
    return render(request,"a_propos.html")

def condition_util(request):
    return render(request,"conditions_util.html")


def politique(request):
    return render(request,"politique.html")




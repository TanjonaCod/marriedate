from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

def membre_validation_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'member'):
            if not request.user.member.validation:  
                return redirect('activer_compte')  
        return view_func(request, *args, **kwargs)
    return wrapper

def condition_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        membre_id = request.session.get("client", {}).get("id")
        from app_membres.models import Profil
        profil = Profil.objects.filter(membre_id=membre_id).first() if membre_id else None
        # Si pas connecté, pas de profil ou profil incomplet (pas de photo), rediriger vers condition_admi
        if not membre_id or not profil or not profil.images:
            return redirect('condition_admi')
        # Si le profil n'est pas validé, rediriger vers attente_validation
        if not getattr(profil, 'valider', False):
            return redirect('Attente_validation')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

from App_activation_inscription.models import Activation_btn
from app_membres.models import Profil

def attente_validation_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        membre_id = request.session.get("client", {}).get("id")

        if not membre_id:
            return redirect('aff_login')

        profil = Profil.objects.filter(membre_id=membre_id).first()

        # Vérifie le statut du bouton d'activation
        activation = Activation_btn.objects.first()
        status_is_actif = activation and activation.status.strip().lower() == 'actif'

        if profil and getattr(profil, 'valider', False):
            return view_func(request, *args, **kwargs)

        if status_is_actif:
            if request.path != '/attente_validation/':
                return redirect('attente_validation')
            return view_func(request, *args, **kwargs)

        # Si inactif, rediriger tous les cas vers membres
        return redirect('membres')
    return _wrapped_view


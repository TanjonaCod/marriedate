# app_accueil/context_processors.py

def profil_image(request):
    if request.user.is_authenticated:
        try:
            return {'profile': request.user.membre.profile}
        except:
            return {'profile': None}
    return {'profile': None}


from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from .views import *
from .views import mon_profil, detail_profil, follow_member, list_followers

urlpatterns = [
    path('', afficher_accueil, name="aff_accueil"),
    path("profile/<int:member_id>/", detail_profil, name="detail_profil"),
    path("profil/<int:profil_id>", mon_profil, name="profil_detail"),
    path("mon_profil/<int:membre_id>/", mon_profil, name="mon_profil"),
    path('follow/<int:member_id>/', follow_member, name='follow_member'),
    path("followers/<int:member_id>/", list_followers, name="list_followers"),
    path('i18n/', include('django.conf.urls.i18n')),
    path("a_propos/",afficher_propos,name="a_propos"),
    path("condition_util/",condition_util,name="condition_util"),
    path("politique/",politique,name="politique"),
]

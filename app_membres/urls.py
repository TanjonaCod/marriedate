from django.urls import path
from .views import *
from .views_block import block_member, unblock_member, blocked_members_list
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('register/', aff_register, name="aff_register"),
    path('register/submit/', enregistrer_membres, name="enregistrer"),
    path('login/', aff_login, name="aff_login"),
    path('login/submit/', connexion_membre, name="connexion_membre"),
    path("condition_admission/", condition, name="condition"),
    path("condition_admi/", condition_admi, name="condition_admi"),
    path("membres/", membre_inscrit, name="membres"),
    path("activer_compte/", activer_compte, name="activer_compte"),
    path("activer_compte/<int:id_user>", valider_activation, name="valider_compte"),
    path("attente_validation/", Attente_validation, name="Attente_validation"),
    path("deconnection/", deconnexion, name="deconnexion"),
    path("like/<int:member_id>/", like_member, name="like_member"),
    path("dislike/<int:member_id>/", dislike_member, name="dislike_member"),
    path("heart/<int:member_id>/", heart_member, name="heart_member"),
    path("ajout_additional/", ajout_additional, name="ajout_additional"),
    path("modifier_profil/", modifier_profil, name="modifier_profil"),
    path("notifications/mark_as_read/", mark_notifications_as_read, name="mark_notifications_as_read"),
    path("upload_profile_image/", upload_profile_image, name="upload_profile_image"),
    path('notifications/', notifications_page, name='notifications_page'),
    path("parametres/suppr/<int:id_membre>/", supprimer_membre_par_id, name="supprimer"),
    path("parametres/<int:id_membre>/", aff_parametres, name="parametres"),
    path("friend_request/send/<int:member_id>/", send_friend_request, name="send_friend_request"),
    path("friend_request/accept/<int:friendship_id>/", accept_friend_request, name="accept_friend_request"),
    path("friends/", list_friends, name="list_friends"),
    path("follow/<int:member_id>/", follow_member, name="follow_member"),
    path("followers/<int:member_id>/", list_followers, name="list_followers"),
    path("changer-mot-de-passe/<int:id_membre>/", changer_mot_de_passe, name="changer_mot_de_passe"),
    path("online/", online_members, name="online_members"),
    path("visitors/<int:member_id>/", list_visitors, name="list_visitors"),
    path('mot-de-passe-oublie/', mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('reset-password/<str:token>/', reset_password, name='reset_password'),
    path('supprimer_photo/', supprimer_photo, name='supprimer_photo'),
    path("parametres/desactiver/<int:id_membre>/",desactiver_membre_par_id,name="desactiver"),
    path('block_member/', block_member, name='block_member'),
    path('unblock_member/', unblock_member, name='unblock_member'),
    path('blocked_members/', blocked_members_list, name='blocked_members_list'),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


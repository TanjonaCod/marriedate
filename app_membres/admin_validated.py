from django.contrib import admin
from .models import Profil
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect

class ProfilValideAdmin(admin.ModelAdmin):
    list_display = ("membre", "sexe", "image_thumb", "valider", "statut_valide")
    list_per_page = 50
    list_filter = ("sexe",)
    
    def image_thumb(self, obj):
        if obj.images:
            return format_html('<img src="{}" width="100" height="100" style="border-radius:6px; box-shadow:0 1px 8px #888;"/>', obj.images.url)
        return "-"
    image_thumb.short_description = "Image"
    image_thumb.allow_tags = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(valider=True)

    def statut_valide(self, obj):
        return "Validé" if obj.valider else "Non validé"
    statut_valide.short_description = "Statut"

    def has_add_permission(self, request):
        return False

# Pour activer cette page, il faut l'enregistrer dans admin.py comme ceci :
# from .admin_validated import ProfilValideAdmin
# admin.site.register(Profil, ProfilValideAdmin)
# Mais attention :
# On ne peut enregistrer le même modèle (Profil) qu'une seule fois dans l'admin Django.
# Pour avoir deux pages séparées dans le menu admin, il faut utiliser un proxy model.

# Exemple de proxy model à ajouter dans models.py :
# class ProfilValide(Profil):
#     class Meta:
#         proxy = True
#         verbose_name = "Profil validé"
#         verbose_name_plural = "Profils validés"

# Puis dans admin.py :
# from .models import ProfilValide
# admin.site.register(ProfilValide, ProfilValideAdmin)

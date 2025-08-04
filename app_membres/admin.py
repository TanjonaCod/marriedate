from django.contrib import admin
from django.urls import path
from .models import Member, Profil, AdditionalProfileInfo
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import AdditionalProfileInfo,validation_automatique
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from .admin_validated import ProfilValideAdmin
from .models import ProfilValide, ProfilNonValide

# Register your models here.
from django.contrib.admin import SimpleListFilter

# Définir le filtre personnalisé AVANT la classe AdminMembres
class InactiveDaysListFilter(SimpleListFilter):
    title = "Jours d'inactivité"
    parameter_name = 'inactive_days'
    def lookups(self, request, model_admin):
        return [
            ('30+', 'Plus de 30 jours'),
            ('60+', 'Plus de 60 jours'),
            ('90+', 'Plus de 90 jours'),
        ]
    def queryset(self, request, queryset):
        from django.utils import timezone
        now = timezone.now()
        if self.value() == '30+':
            return queryset.filter(user__last_login__lt=now - timezone.timedelta(days=30))
        if self.value() == '60+':
            return queryset.filter(user__last_login__lt=now - timezone.timedelta(days=60))
        if self.value() == '90+':
            return queryset.filter(user__last_login__lt=now - timezone.timedelta(days=90))
        return queryset

class AdminMembres(admin.ModelAdmin):
    list_display = ("pseudo","email","country","date_inscrit","last_active_display","days_inactive","is_active")
    search_fields = ("pseudo", "email")
    list_filter = ("country", "is_active", "date_inscrit", InactiveDaysListFilter)
    def days_inactive(self, obj):
        from django.utils import timezone
        if obj.activiter_dernier:
            delta = timezone.now() - obj.activiter_dernier
            return delta.days
        return "-"
    days_inactive.short_description = "Jours d'inactivité"

    def last_active_display(self, obj):
        return obj.activiter_dernier if obj.activiter_dernier else "-"
    last_active_display.short_description = "Dernière activité"

from django.contrib.admin import SimpleListFilter

class InactiveDaysListFilter(SimpleListFilter):
    title = 'Jours d\'inactivité'
    parameter_name = 'inactive_days'

    def lookups(self, request, model_admin):
        return [
            ('30+', 'Plus de 30 jours'),
            ('60+', 'Plus de 60 jours'),
            ('90+', 'Plus de 90 jours'),
        ]

    def queryset(self, request, queryset):
        from django.utils import timezone
        now = timezone.now()
        if self.value() == '30+':
            return queryset.filter(user__last_login__lt=now - timezone.timedelta(days=30))
        if self.value() == '60+':
            return queryset.filter(user__last_login__lt=now - timezone.timedelta(days=60))
        if self.value() == '90+':
            return queryset.filter(user__last_login__lt=now - timezone.timedelta(days=90))
        return queryset
    list_per_page = 50  
    actions = ["delete_inactive_members"]
    def delete_inactive_members(self, request, queryset):
        from datetime import timedelta, datetime
        from django.utils import timezone
        threshold_days = 30  # Modifier ici pour changer la période d'inactivité
        now = timezone.now()
        count = 0
        for member in queryset:
            last_login = member.user.last_login if member.user and hasattr(member.user, 'last_login') else None
            if last_login and (now - last_login).days > threshold_days:
                member.user.delete()  # Supprime aussi le Member via cascade
                count += 1
        self.message_user(request, f"{count} membre(s) inactif(s) supprimé(s) (inactifs depuis plus de {threshold_days} jours).")
    delete_inactive_members.short_description = "Supprimer les membres inactifs depuis plus de 30 jours"


    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(Member,AdminMembres)


class ProfilPlus(admin.ModelAdmin):
    list_display = ("image1_thumb", "image2_thumb", "image3_thumb", "image4_thumb", "image5_thumb","image6_thumb")
    
    list_per_page = 50  

    def image1_thumb(self, obj):
        return self._image_with_delete(obj, 1)
    def image2_thumb(self, obj):
        return self._image_with_delete(obj, 2)
    def image3_thumb(self, obj):
        return self._image_with_delete(obj, 3)
    def image4_thumb(self, obj):
        return self._image_with_delete(obj, 4)
    def image5_thumb(self, obj):
        return self._image_with_delete(obj, 5)
    def image6_thumb(self, obj):
        return self._image_with_delete(obj, 6)

    image1_thumb.short_description = "Image 1"
    image2_thumb.short_description = "Image 2"
    image3_thumb.short_description = "Image 3"
    image4_thumb.short_description = "Image 4"
    image5_thumb.short_description = "Image 5"
    image6_thumb.short_description = "Image 6"

    def _image_with_delete(self, obj, num):
        image_field = getattr(obj, f"additional_image{num}")
        if image_field:
            img_html = f'<div style="text-align:center;"><img src="{image_field.url}" width="200" style="display:block; margin:auto; border-radius:6px; box-shadow:0 1px 8px #888; margin-bottom:8px;"/></div>'
            delete_url = f"/admin/app_membres/additionalprofileinfo/{obj.id}/delete_image/{num}/"
            btn_html = (
                '<div style="text-align:center;">'
                '<a href="{}" style="display:inline-block; padding:6px 16px; background:#e74c3c; color:white; border-radius:4px; text-decoration:none; font-weight:bold; margin-top:4px;" '
                'onclick="return confirm(\'Supprimer cette image ?\')">'
                '<i class="fa fa-trash" style="margin-right:5px;"></i>Supprimer'
                '</a>'
                '</div>'
            ).format(delete_url)
            return format_html(f'{img_html}{btn_html}')
        return "-"


    def get_urls(self):
        urls = super().get_urls()
        from django.urls import re_path
        custom_urls = [
            re_path(r'^(?P<obj_id>\d+)/delete_image/(?P<num>[1-6])/$', self.admin_site.admin_view(self.delete_image), name='delete_additional_image'),
        ]
        return custom_urls + urls

    def delete_image(self, request, obj_id, num):
        obj = get_object_or_404(AdditionalProfileInfo, id=obj_id)
        field_name = f"additional_image{num}"
        image_field = getattr(obj, field_name)
        if image_field:
            image_field.delete(save=False)
            setattr(obj, field_name, None)
            obj.save()
            self.message_user(request, f"Image {num} supprimée.")
        else:
            self.message_user(request, f"Aucune image à supprimer.", level="error")
        return redirect(request.META.get('HTTP_REFERER', '/admin/app_membres/additionalprofileinfo/'))

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(AdditionalProfileInfo,ProfilPlus)

class ProfilMembres(admin.ModelAdmin):
    list_display = ("membre", "sexe", "images", "valider", "action_valider")
    list_per_page = 50  # Pagination par 50
    list_filter = ("valider", "sexe")  # Ajoute un filtre pour valider/non validé et sexe

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Ajoute un attribut pour distinguer les profils validés automatiquement
        for profil in qs:
            profil.valide_auto = profil.sexe != "Femme"  # Exemple : tous les hommes sont validés automatiquement
        return qs

    def action_valider(self, obj):
        if obj.sexe == "Femme":
            button_text = "Non Valider" if not obj.valider else "Validé"
            button_color = "red" if not obj.valider else "green"
            url = reverse('admin:valider_profil', args=[obj.id])
            return format_html(
                '<a class="button" style="color: white; background-color: {}" href="{}">{}</a>',
                button_color,
                url,
                button_text
            )
        return "Validé automatiquement"

    action_valider.short_description = "Action de validation"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('profil/<int:profil_id>/', self.valider_profil, name='valider_profil'),
        ]
        return custom_urls + urls

    def valider_profil(self, request, profil_id):
        try:
            profil = Profil.objects.get(id=profil_id)
            profil.valider = True
            profil.save()
            self.message_user(request, f"Le profil de {profil.membre} a été validé avec succès.")
        except Profil.DoesNotExist:
            self.message_user(request, "Profil introuvable.", level="error")
        return HttpResponseRedirect(reverse('admin:app_membres_profil_changelist'))

    def has_add_permission(self, request):
        return False
    # def has_change_permission(self, request, obj=None):
    #     return False
    
admin.site.register(Profil,ProfilMembres)
# admin.site.register(AdditionalProfileInfo)

class ValiderAuto(admin.ModelAdmin):
    list_display = ("autorisation", "toggle_button")
    
    def toggle_button(self, obj):
        if obj.autorisation:
            button_style = "background-color: green; color: white"
            button_text = "Désactiver"
        else:
            button_style = "background-color: red; color: white"
            button_text = "Activer"
            
        return format_html(
            '<a class="button" href="{}" style="{}">{}</a>',
            reverse('admin:toggle_validation', args=[obj.pk]),
            button_style,
            button_text
        )
    toggle_button.short_description = "Action"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('toggle/<int:validation_id>/', self.toggle_validation, name='toggle_validation'),
        ]
        return custom_urls + urls

    def toggle_validation(self, request, validation_id):
        validation = validation_automatique.objects.get(id=validation_id)
        validation.autorisation = not validation.autorisation
        validation.save()
        
        if validation.autorisation:
            # Valider automatiquement tous les profils femmes non validés
            Profil.objects.filter(sexe="Femme", valider=False).update(valider=True)
            self.message_user(request, "Validation automatique activée et tous les profils femmes ont été validés")
        else:
            self.message_user(request, "Validation automatique désactivée")
            
        return redirect('admin:app_membres_validation_automatique_changelist')
    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(validation_automatique, ValiderAuto)

# Ajout des admins pour les profils validés et non validés
class ProfilNonValideAdmin(admin.ModelAdmin):
    list_display = ("membre", "sexe", "image_thumb", "valider", "action_valider")
    list_per_page = 50
    list_filter = ("sexe",)

    def image_thumb(self, obj):
        if obj.images:
            return format_html('<img src="{}" width="100" height="100" style="border-radius:6px; box-shadow:0 1px 8px #888;"/>', obj.images.url)
        return "-"
    image_thumb.short_description = "Image"
    image_thumb.allow_tags = True

    # Changer le nom de l'entrée admin dans le menu
    def get_model_perms(self, request):
        # Affiche l'entrée dans le menu admin
        return super().get_model_perms(request)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(valider=False)

    def action_valider(self, obj):
        if obj.sexe == "Femme":
            button_text = "Non Valider" if not obj.valider else "Validé"
            button_color = "red" if not obj.valider else "green"
            url = reverse('admin:valider_profil_nonvalide', args=[obj.id])
            return format_html(
                '<a class="button" style="color: white; background-color: {}" href="{}">{}</a>',
                button_color,
                url,
                button_text
            )
        return "Validé automatiquement"
    action_valider.short_description = "Action de validation"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('profil/<int:profil_id>/', self.valider_profil, name='valider_profil_nonvalide'),
        ]
        return custom_urls + urls

    def valider_profil(self, request, profil_id):
        try:
            profil = Profil.objects.get(id=profil_id)
            profil.valider = True
            profil.save()
            self.message_user(request, f"Le profil de {profil.membre} a été validé avec succès.")
        except Profil.DoesNotExist:
            self.message_user(request, "Profil introuvable.", level="error")
        return HttpResponseRedirect(reverse('admin:app_membres_profilnonvalide_changelist'))

    def has_add_permission(self, request):
        return False

    # Changer le nom de l'entrée admin dans le menu
    def get_admin_name(self):
        return "Profils non validés"
    get_admin_name.short_description = "Profils non validés"

    @property
    def verbose_name(self):
        return "Profils non validés"
    
    @property
    def verbose_name_plural(self):
        return "Profils non validés"

# Enregistrement du proxy model pour les profils validés
admin.site.register(ProfilValide, ProfilValideAdmin)

# class ProfilValideAdmin(admin.ModelAdmin):
#     list_display = ("membre", "sexe", "images", "valider", "action_valider")
#     list_per_page = 50
#     list_filter = ("sexe",)

#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.filter(valider=True)

#     def action_valider(self, obj):
#         return "Validé" if obj.valider else "Non validé"
#     action_valider.short_description = "Statut"

#     def has_add_permission(self, request):
#         return False

# Désenregistrer l'ancien admin et enregistrer les deux nouveaux
try:
    admin.site.unregister(Profil)
except admin.sites.NotRegistered:
    pass
# Enregistrement du proxy model pour afficher l'entrée "Profils non validés" dans l'admin
admin.site.register(ProfilNonValide, ProfilNonValideAdmin)

# Pour voir les profils validés, il faut utiliser un filtre dans l'admin (colonne de droite)
# ou créer une vue personnalisée si tu veux vraiment deux pages séparées dans le menu admin.



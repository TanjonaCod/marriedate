from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin
from django.shortcuts import redirect, get_object_or_404
from .models import Photo

from django.urls import path

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('membre_nom', 'date', 'valider', 'valider_action', 'image_thumb', 'valider_bouton')
    list_filter = ('valider',)
    actions = ['valider_photos']
    list_per_page = 50
    search_fields = ('membre_nom', 'membre_email')
    
    def image_thumb(self, obj):
        if obj.images:
            return format_html('<img src="{}" style="border-radius:6px; box-shadow:0 1px 8px #888; max-width:100vw; width:100%; height:auto;"/>', obj.images.url)
        return "-"

    @admin.action(description="Valider les photos sélectionnées")
    def valider_photos(self, request, queryset):
        updated = queryset.update(valider=True)
        self.message_user(request, f"{updated} photo(s) validée(s) avec succès ✅")

    def valider_action(self, obj):
        return "✅ Validée" if obj.valider else "⛔ Non validée"
    valider_action.short_description = "Statut"

    def valider_bouton(self, obj):
        if not obj.valider:
            url = reverse("admin:valider_photo", args=[obj.id])
            return format_html('<a class="button" style="color:red;" href="{}">Valider</a>', url)
        return "-"
    valider_bouton.short_description = "Validation directe"

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

    def images(self, obj):
        image = getattr(obj, 'image', None)
        if image:
            url = str(image)
            if url.startswith('http://') or url.startswith('https://') or url.startswith('/static/') or url.startswith('/'):
                pass
            else:
                url = '/static/images/' + url.lstrip('/')
            return format_html('<a href="{}" target="_blank" style="display:inline-block; padding:6px 14px; background:#3498db; color:white; border-radius:4px; text-decoration:none; font-weight:bold;">Voir image</a>', url)
        return "-"
    images.short_description = "Image"


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('valider/<int:photo_id>/', self.admin_site.admin_view(self.valider_view), name='valider_photo'),
        ]
        return custom_urls + urls

    def valider_view(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        photo.valider = True
        photo.save()
        self.message_user(request, f"La photo de {photo.membre_nom} a été validée ✅")
        return redirect(request.META.get('HTTP_REFERER', 'admin:app_photo_changelist'))

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

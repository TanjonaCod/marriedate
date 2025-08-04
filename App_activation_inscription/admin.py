from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from .models import Activation_btn

class Dash_activation_inscriction(admin.ModelAdmin):
    list_display = ('status', 'toggle_status_button')

    def toggle_status_button(self, obj):
        if obj.status.lower() == 'actif':
            return format_html(
                '<a class="button" style="color:red;" href="{}">Désactiver</a>',
                f'toggle-status/{obj.pk}/'
            )
        else:
            return format_html(
                '<a class="button" style="color:green;" href="{}">Activer</a>',
                f'toggle-status/{obj.pk}/'
            )
    toggle_status_button.short_description = 'Changer status'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('toggle-status/<int:pk>/', self.admin_site.admin_view(self.toggle_status), name='toggle_status'),
        ]
        return custom_urls + urls

    def toggle_status(self, request, pk):
        obj = Activation_btn.objects.get(pk=pk)
        if obj.status.lower() == 'actif':
            obj.status = 'Inactif'
        else:
            obj.status = 'Actif'
        obj.save()
        self.message_user(request, f"Status modifié pour {obj}")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

admin.site.register(Activation_btn, Dash_activation_inscriction)

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render

def contact(request):
    message_envoye = False
    erreur = None
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        if name and email and message:
            try:
                send_mail(
                    subject=f"[Contact LoveMeet] Message de {name}",
                    message=f"Nom: {name}\nEmail: {email}\n\nMessage:\n{message}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=["lovelimeet123@gmail.com"],
                )
                message_envoye = True
            except Exception as e:
                erreur = "Erreur lors de l'envoi de l'email. Veuillez réessayer."
        else:
            erreur = "Tous les champs sont obligatoires."
    return render(request, 'contact.html', {'message_envoye': message_envoye, 'erreur': erreur})

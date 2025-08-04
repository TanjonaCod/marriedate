from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import dns.resolver
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.contrib.auth.models import User
import logging
logger = logging.getLogger(__name__)
from datetime import date, timedelta
from PIL import Image

def valid_email(value):
    if "fuck" in value.lower():
        raise ValidationError("Cet email est inapproprié.")

def validate_email_domain(email):
    domain = email.split('@')[-1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return False

def validate_email(value):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, value):
        raise ValidationError('Format email invalide.')
    
    if not validate_email_domain(value):
        raise ValidationError('Domaine email invalide ou inexistant.')
    
    valid_email(value)

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member",unique=True,null=True)
    pseudo = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True, validators=[validate_email])
    birthdate = models.DateField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    lieux = models.CharField(max_length=100,null=True)
    gender = models.CharField(max_length=10)
    looking_for = models.CharField(max_length=10)
    password = models.CharField(max_length=100)
    terms_accepted = models.BooleanField(default=False)
    age_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)
    date_inscrit = models.DateTimeField(auto_now_add=True)
    activiter_dernier = models.DateTimeField(null=True, blank=True)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    reset_token_created = models.DateTimeField(null=True, blank=True)
    age_debut = models.IntegerField(null=True,blank=True)
    age_fin = models.IntegerField(null=True,blank=True)
    desactivation = models.BooleanField(default=False)
    blocked_members = models.ManyToManyField('self', symmetrical=False, related_name='blocked_by', blank=True)

    def __str__(self):
        return self.pseudo

    def caluler_age(self):
        today = date.today()
        return today.year - self.birthdate.year - (
            (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
        )

    @property
    def is_online(self):
        if self.activiter_dernier:
            return now() - self.activiter_dernier < timedelta(minutes=5)  # Considérer comme en ligne si actif dans les 5 dernières minutes
        return False

    @property
    def likes_received_count(self):
        return self.likes_received.count()

    @property
    def dislikes_received_count(self):
        return self.dislikes_received.count()

    @property
    def notifications_count(self):
        return self.likes_received.count()  # Adjust this to your actual notifications logic

    @property
    def hearts_received_count(self):
        return self.hearts_received.count()

    def update_likes_count(self, session):
        session["client"]["likes_count"] = self.likes_received_count
        session.modified = True

    def update_notifications_count(self, session):
        session["client"]["notifications_count"] = self.notifications_count
        session.modified = True

    def __str__(self):
        return self.pseudo

    def is_valid_email(self):
        try:
            validate_email(self.email)
            return True
        except ValidationError:
            return False

class Profil(models.Model):
    CHEVEUX_CHOICES = [
        ('blond', 'Blond'),
        ('gris', 'Gris'),
        ('marron', 'Marron'),
        ('noir', 'Noir'),
        ('change', 'Je change souvent'),
        ('chatain', 'Châtain'),
        ('autre', 'Autre'),
    ]
    
    membre = models.OneToOneField(Member, on_delete=models.CASCADE,null=True)
    sexe = models.CharField(max_length=10)
    cheveux = models.CharField(max_length=20, choices=CHEVEUX_CHOICES)
    yeux = models.CharField(max_length=20)
    taille = models.IntegerField()
    poids = models.IntegerField()
    alcool = models.CharField(max_length=20)
    tabac = models.CharField(max_length=20)
    situation = models.CharField(max_length=20)
    enfants = models.IntegerField()
    description = models.TextField()
    recherche = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    images = models.ImageField(upload_to="profils/")
    valider = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  
        
        img = Image.open(self.images)

        max_size = (10000, 200)  
        if img.height > 200 or img.width > 300:
            img.thumbnail(max_size)  
            img.save(self.images)  

    def __str__(self):
        return str(self.images)

    def save(self, *args, **kwargs):
        if not self.pk:  # Nouveau profil
            if self.sexe == "Homme" or validation_automatique.is_auto_validation_enabled():
                self.valider = True
        super().save(*args, **kwargs)

class ProfilNonValide(Profil):
    class Meta:
        proxy = True
        verbose_name = "Profil non validé"
        verbose_name_plural = "Profils non validés"

class ProfilValide(Profil):
    class Meta:
        proxy = True
        verbose_name = "Profil validé"
        verbose_name_plural = "Profils validés"

class Like(models.Model):
    liker = models.ForeignKey(Member, related_name='likes_given', on_delete=models.CASCADE)
    liked = models.ForeignKey(Member, related_name='likes_received', on_delete=models.CASCADE)
    date_liked = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('liker', 'liked')

    def __str__(self):
        return f"{self.liker.pseudo} aime {self.liked.pseudo}"

class Dislike(models.Model):
    disliker = models.ForeignKey(Member, related_name='dislikes_given', on_delete=models.CASCADE)
    disliked = models.ForeignKey(Member, related_name='dislikes_received', on_delete=models.CASCADE)
    date_disliked = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('disliker', 'disliked')

class Heart(models.Model):
    giver = models.ForeignKey(Member, related_name='hearts_given', on_delete=models.CASCADE)
    receiver = models.ForeignKey(Member, related_name='hearts_received', on_delete=models.CASCADE)
    date_given = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('giver', 'receiver')

    def __str__(self):
        return f"{self.giver.pseudo} a donné un cœur à {self.receiver.pseudo}"

class AdditionalProfileInfo(models.Model):
    membre = models.OneToOneField(Member, on_delete=models.CASCADE,null=True)
    ethnicite = models.CharField(max_length=100, blank=True, null=True)
    art_corporel = models.CharField(max_length=100, blank=True, null=True)
    enfants_souhaites = models.CharField(max_length=100, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    situation_vie = models.CharField(max_length=100, blank=True, null=True)
    demenagement = models.CharField(max_length=100, blank=True, null=True)
    relation_recherche = models.CharField(max_length=100, blank=True, null=True)
    niveau_etude = models.CharField(max_length=100, blank=True, null=True)
    religion = models.CharField(max_length=100, blank=True, null=True)
    signe_astrologique = models.CharField(max_length=100, blank=True, null=True)
    additional_image1 = models.ImageField(upload_to="static/images/membres/", blank=True, null=True)
    additional_image2 = models.ImageField(upload_to="static/images/membres/", blank=True, null=True)
    additional_image3 = models.ImageField(upload_to="static/images/membres/", blank=True, null=True)
    additional_image4 = models.ImageField(upload_to="static/images/membres/", blank=True, null=True)
    additional_image5 = models.ImageField(upload_to="static/images/membres/", blank=True, null=True)
    additional_image6 = models.ImageField(upload_to="static/images/membres/", blank=True, null=True)
   

    def __str__(self):
        return f"Additional Info for {self.membre.pseudo}"

class Notification(models.Model):
    recipient = models.ForeignKey(Member, related_name='app_membres_notifications', on_delete=models.SET_NULL, null=True,blank=True)
    sender = models.ForeignKey(
        Member, 
        related_name="sent_notifications", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    message = models.TextField()
    url = models.CharField(max_length=255, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Notification for {self.recipient.username if self.recipient else 'Unknown'} from {self.sender.pseudo if self.sender else 'System'}"

class Friendship(models.Model):
    sender = models.ForeignKey(
        Member, 
        related_name="friend_requests_sent", 
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        Member, 
        related_name="friend_requests_received", 
        on_delete=models.CASCADE
    )
    is_accepted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.pseudo} -> {self.receiver.pseudo} ({'Accepted' if self.is_accepted else 'Pending'})"

class Follower(models.Model):
    follower = models.ForeignKey(Member, related_name="following", on_delete=models.CASCADE)
    followed = models.ForeignKey(Member, related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_followers(member):
        return Follower.objects.filter(followed=member)

    @staticmethod
    def get_following(member):
        return Follower.objects.filter(follower=member)

    def __str__(self):
        return f"{self.follower.pseudo} follows {self.followed.pseudo}"


class validation_automatique(models.Model):
    autorisation = models.BooleanField(default=False)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Validation Automatique"
        verbose_name_plural = "Validations Automatiques"

    def __str__(self):
        status = "Activée" if self.autorisation else "Désactivée"
        return f"Validation automatique ({status})"

    @classmethod
    def is_auto_validation_enabled(cls):
        return cls.objects.filter(autorisation=True).exists()

class ProfileVisit(models.Model):
    visitor = models.ForeignKey(Member, related_name='profile_visits', on_delete=models.CASCADE)
    visited = models.ForeignKey(Member, related_name='profile_visitors', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        unique_together = ['visitor', 'visited']

    def __str__(self):
        return f"{self.visitor.pseudo} a visité {self.visited.pseudo}"

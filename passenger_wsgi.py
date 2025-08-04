import os
import sys

# Ajouter le chemin du projet à sys.path
sys.path.insert(0, "C:/wamp64/www/lovelimeetapp")

# Définir le module de configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "site_rencontre.settings")

# Charger l'application WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

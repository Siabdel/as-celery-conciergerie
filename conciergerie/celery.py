
from __future__ import absolute_import
import os
from django.conf import settings
from celery import Celery

# Indique à Celery où trouver les settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conciergerie.settings')
app = Celery('conciergerie')

# Charger les configurations de Celery depuis le fichier settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches de toutes les applications installées
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

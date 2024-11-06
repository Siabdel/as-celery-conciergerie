
from __future__ import absolute_import
import os
from django.conf import settings
from celery import Celery, shared_task
## from django_celery_beat.models import PeriodicTask, CrontabSchedule

# Indique à Celery où trouver les settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')

# Charger les configurations de Celery depuis le fichier settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches de toutes les applications installées
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

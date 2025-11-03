from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaytri_farm_app.settings')

# Create Celery app
app = Celery('gaytri_farm_app')

# Load config from Django settings, namespace='CELERY' means
# all celery-related settings start with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs
app.autodiscover_tasks()


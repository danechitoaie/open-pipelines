# System
from os import environ

# Celery
from celery import Celery


# Set the default settings module for the 'celery' program
environ.setdefault("DJANGO_SETTINGS_MODULE", "open_pipelines.settings")

app = Celery("open_pipelines")

# Using a string here means the worker don't have to serialize
# the configuration object to child processes
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered apps
app.autodiscover_tasks()
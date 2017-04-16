"""
WSGI config for open_pipelines2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

from os               import environ
from django.core.wsgi import get_wsgi_application

environ.setdefault("DJANGO_SETTINGS_MODULE", "open_pipelines.settings")
application = get_wsgi_application()

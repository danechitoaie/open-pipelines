# Django
from django.conf import settings


def build_absolute_uri(relative_url):
    return "{0}{1}".format(
        settings.OPEN_PIPELINES_BASE_URL, 
        relative_url
    )
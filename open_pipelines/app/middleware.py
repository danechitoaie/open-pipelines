# Django
from django.conf              import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional  import SimpleLazyObject

# Open Pipelines
from .models import User


def get_user(request):
    if not hasattr(request, "_cached_user"):
        if not "user_uuid" in request.session:
            request._cached_user = None
            return request._cached_user

        try:
            request._cached_user = User.objects.get(pk=request.session.get("user_uuid"))
        except User.DoesNotExist:
            request._cached_user = None

    return request._cached_user


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), "The authentication middleware requires session middleware to be installed."
        request.user = SimpleLazyObject(lambda: get_user(request))

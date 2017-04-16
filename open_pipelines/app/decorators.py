# Django
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse


def login_required(f):
    def wrap(self, request, *args, **kwargs):
        if not request.user:
            return HttpResponseRedirect(reverse("login"))
        return f(self, request, *args, **kwargs)
    return wrap


def login_required_json(f):
    def wrap(self, request, *args, **kwargs):
        if not request.user:
            return JsonResponse({
                "status" : "unauthorized"
            }, status=401)
        return f(self, request, *args, **kwargs)
    return wrap
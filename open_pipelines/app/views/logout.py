from django.views.generic import View
from django.urls          import reverse
from django.http          import HttpResponseRedirect

class LogoutView(View):
    def get(self, request):
        request.session.flush()
        return HttpResponseRedirect(reverse("login"))

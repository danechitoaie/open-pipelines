# System
from datetime import timedelta

# Django
from django.utils         import timezone
from django.views.generic import View
from django.shortcuts     import render
from django.shortcuts     import redirect
from django.urls          import reverse
from django.http          import Http404

# Open Pipelines
from ..models   import User
from ..services import ServiceManager


class LoginView(View):
    def get(self, request):
        service_manager = ServiceManager()
        return render(request, "login.html", {
            "services" : service_manager.get_services()
        })

class LoginWithServiceView(View):
    def get(self, request, service_id):
        service_manager = ServiceManager()

        try:
            service = service_manager.get_service(service_id)
        except ServiceManager.DoesNotExist:
            raise Http404()

        # User was redirected back with an error
        if request.GET.get("error") != None:
            return render(request, "login_error.html")

        # User was redirected back with an authorization code
        if request.GET.get("code") != None:
            oauth_code = request.GET.get("code")
            oauth_data = service.process_oauth(oauth_code)

            if oauth_data == None:
                return render(request, "login_error.html")

            user, \
            user_created = User.objects.update_or_create(
                username = "{0}:{1}".format(service.get_id(), oauth_data.get("username")),
                defaults = {
                    "display_name"    : oauth_data.get("display_name"),
                    "service_id"      : service.get_id(),
                    "service_username": oauth_data.get("username"),
                    "service_atoken"  : oauth_data.get("atoken"),
                    "service_rtoken"  : oauth_data.get("rtoken"),
                    "service_etoken"  : oauth_data.get("etoken"),
                    "last_login"      : timezone.now(),
                }
            )

            request.session.flush()
            request.session["user_uuid"] = str(user.uuid)
            return redirect(reverse("index"))

        # Redirect user to OAuth2 page
        return redirect(service.get_oauth_url())

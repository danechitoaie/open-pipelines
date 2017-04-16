# Django
from django.views.generic import View
from django.http          import JsonResponse
from django.urls          import reverse

# Open Pipelines
from ..util       import build_absolute_uri
from ..decorators import login_required_json
from ..models     import Repo
from ..services   import ServiceManager


class ReposJsonView(View):
    @login_required_json
    def get(self, request):
        service_manager = ServiceManager()
        request_user    = request.user

        try:
            service = service_manager.get_service(request_user.service_id)
        except ServiceManager.DoesNotExist:
            return JsonResponse({
                "status" : "error"
            }, status=500)

        page = 1
        if "p" in request.GET:
            try:
                page = int(request.GET.get("p"))
            except:
                pass

        data = service.get_repos(request_user, page)
        if data == None:
            return JsonResponse({
                "status" : "error"
            })

        return JsonResponse({
            "status" : "ok",
            "data"   : data,
        })

class RepoByPathJsonView(View):
    @login_required_json
    def get(self, request, repo_path):
        try:
            repo = request.user.repo_set.get(path=repo_path)
        except Repo.DoesNotExist:
            return JsonResponse({
                "status" : "not_found"
            }, status=404)

        if not repo.enabled:
            return JsonResponse({
                "status" : "not_found"
            }, status=404)

        return JsonResponse({
            "status"  : "ok",
            "enabled" : repo.enabled,
            "public"  : repo.public,
            "webhook" : build_absolute_uri(reverse("webhook_by_uuid", args=[repo.uuid])),
        })

    @login_required_json
    def post(self, request, repo_path):
        service_manager = ServiceManager()
        request_user    = request.user

        try:
            service = service_manager.get_service(request_user.service_id)
        except ServiceManager.DoesNotExist:
            return JsonResponse({
                "status" : "error"
            }, status=500)

        # Request to enable
        if request.POST.get("method") == "enable":
            repo, repo_created = Repo.objects.update_or_create(
                user     = request.user,
                path     = repo_path,
                defaults = {
                    "enabled" : True,
                    "public"  : False,
                },
            )

            return JsonResponse({
                "status"  : "ok",
                "enabled" : repo.enabled,
                "public"  : repo.public,
                "webhook" : build_absolute_uri(reverse("webhook_by_uuid", args=[repo.uuid])),
            })

        # Request to disable
        if request.POST.get("method") == "disable":
            repo, repo_created = Repo.objects.update_or_create(
                user     = request.user,
                path     = repo_path,
                defaults = {
                    "enabled" : False,
                    "public"  : False,
                },
            )

            return JsonResponse({
                "status"  : "ok",
                "enabled" : repo.enabled,
                "public"  : repo.public,
            })

        # Request to make public
        if request.POST.get("method") == "public":
            repo, repo_created = Repo.objects.update_or_create(
                user     = request.user,
                path     = repo_path,
                defaults = {"public" : True},
            )
            return JsonResponse({
                "status" : "ok",
                "public" : repo.public,
            })

        # Request to make private
        if request.POST.get("method") == "private":
            repo, repo_created = Repo.objects.update_or_create(
                user     = request.user,
                path     = repo_path,
                defaults = {"public" : False},
            )
            return JsonResponse({
                "status" : "ok",
                "public" : repo.public,
            })

        return JsonResponse({
            "status": "bad_request"
        }, status=400)

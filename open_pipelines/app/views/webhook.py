# Django
from django.views.generic import View
from django.http          import HttpResponse

# Open Pipelines
from ..models   import Repo
from ..models   import Build
from ..services import ServiceManager
from ..tasks    import run_pipeline


class WebhookByUUIDView(View):
    def post(self, request, repo_uuid):
        try:
            repo = Repo.objects.get(pk=repo_uuid)
        except (ValueError, Repo.DoesNotExist):
            return HttpResponse("Not Found", status=404)

        if not repo.enabled:
            return HttpResponse("Not Found", status=404)

        service_manager = ServiceManager()
        user            = repo.user

        try:
            service = service_manager.get_service(user.service_id)
        except ServiceManager.DoesNotExist:
            return HttpResponse("Internal Server Error", status=500)

        webhook_data = service.parse_webhook_request(request.body)
        if webhook_data == None:
            return HttpResponse("Bad Request", status=400)

        webhook_repo_path = webhook_data.get("repo_path")
        webhook_changes   = webhook_data.get("changes")

        if webhook_repo_path != repo.path:
            return HttpResponse("Forbidden", status=403)

        for c in webhook_changes:
            build = Build(
                repo                = repo,
                ref                 = c.get("ref"),
                commit              = c.get("commit"),
                message             = c.get("message"),
                author_username     = c.get("author_username"),
                author_display_name = c.get("author_display_name"),
                status              = "PENDING",
            )
            build.save()
            run_pipeline.delay(build_uuid=str(build.uuid))

        return HttpResponse("OK", content_type="text/plain")
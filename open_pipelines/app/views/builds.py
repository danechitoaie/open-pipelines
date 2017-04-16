# System
from datetime     import datetime
from urllib.parse import urlencode

# Django
from django.views.generic import View
from django.shortcuts     import render
from django.http          import Http404
from django.utils         import timezone
from django.http          import JsonResponse
from django.urls          import reverse

# Humanize
import humanize

# Open Pipelines
from ..models   import Build
from ..services import ServiceManager


class BuildByUUIDView(View):
    def get(self, request, build_uuid):
        try:
            build = Build.objects.get(pk=build_uuid)
        except (ValueError, Build.DoesNotExist):
            raise Http404()

        service_manager = ServiceManager()
        repo            = build.repo
        user            = repo.user

        try:
            service = service_manager.get_service(user.service_id)
        except ServiceManager.DoesNotExist:
            raise Http404()

        if not repo.enabled:
            raise Http404()

        if not repo.public:
            if not request.user:
                raise Http404()

            if str(request.user.uuid) != str(user.uuid):
                raise Http404()

        return render(request, "build.html", {
            "build_uuid"                : str(build.uuid),
            "build_status"              : build.status,
            "build_author_href"         : service.get_user_href(user),
            "build_author_display_name" : build.author_display_name,
            "build_ref"                 : build.ref,
            "build_commit"              : build.commit,
            "build_message"             : build.message,
        })

class BuildByUUIDJsonView(View):
    def get(self, request, build_uuid):
        try:
            build = Build.objects.get(pk=build_uuid)
        except (ValueError, Build.DoesNotExist):
            return JsonResponse({
                "status" : "not_found"
            }, status=404)

        service_manager = ServiceManager()
        repo            = build.repo
        user            = repo.user

        try:
            service = service_manager.get_service(user.service_id)
        except ServiceManager.DoesNotExist:
            return JsonResponse({
                "status" : "not_found"
            }, status=404)

        if not repo.enabled:
            return JsonResponse({
                "status" : "not_found"
            }, status=404)

        if not repo.public:
            if not request.user:
                return JsonResponse({
                    "status" : "not_found"
                }, status=404)

            if str(request.user.uuid) != str(user.uuid):
                return JsonResponse({
                    "status" : "not_found"
                }, status=404)

        datetime_start = None
        if build.datetime_start != None:
            datetime_start = datetime.strftime(build.datetime_start, "%Y-%m-%d %H:%M:%S %z")

        datetime_elapsed = None
        if build.datetime_start != None and build.datetime_end != None:
            datetime_elapsed = humanize.naturaldelta(build.datetime_end - build.datetime_start)

        build_output   = build.output
        build_url_more = None

        if build.status == "INPROGRESS":
            build_url_more = "{0}?{1}".format(reverse("build_by_uuid_json", args=[build_uuid]), urlencode({
                "after" : len(build_output)
            }))

        after = 0
        if "after" in request.GET:
            try:
                after = int(request.GET.get("after"))
            except:
                pass

        if after > 0:
            build_output = build_output[after:]

        return JsonResponse({
            "status"                 : "ok",
            "build_status"           : build.status,
            "build_datetime_start"   : datetime_start,
            "build_datetime_elapsed" : datetime_elapsed,
            "build_docker_image"     : build.docker_image,
            "build_output"           : build_output,
            "build_url_more"         : build_url_more,
        })

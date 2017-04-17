# System
import tempfile
import os
import subprocess
import shutil
import urllib.parse

# Celery
from celery import shared_task

# Django
from django.urls  import reverse
from django.utils import timezone

# Open Pipelines
from .models   import Build
from .services import ServiceManager

# PyYAML
import yaml

# Docker
import docker


@shared_task
def run_pipeline(build_uuid):
    try:
        build = Build.objects.get(pk=build_uuid)
    except Exception as e:
        return "FAILED Exception = {0}".format(e)

    service_manager = ServiceManager()
    repo            = build.repo
    repo_user       = repo.user

    try:
        service = service_manager.get_service(repo_user.service_id)
    except Exception as e:
        return "FAILED Exception = {0}".format(e)

    try:
        # Build started
        build.status = "INPROGRESS"
        build.datetime_start = timezone.now()
        build.save(update_fields=["status", "datetime_start"])

        # Build Status = INPROGRESS
        service.set_build_status(build, "INPROGRESS")

        with tempfile.TemporaryDirectory(prefix="pipeline_") as ws_name:
            build.output = ""

            pth_sh = os.path.join(os.path.realpath(ws_name), "sh")
            pth_ws = os.path.join(os.path.realpath(ws_name), "ws")

            os.mkdir(pth_sh)
            os.mkdir(pth_ws)

            oauth_atoken = urllib.parse.quote(repo_user.service_atoken)

            # Docker step
            open_pipelines_yml = service.get_open_pipelines_yml(build)
            if open_pipelines_yml == None:
                build.output      += "\n"
                build.output      += "ERROR: Failed to get open_pipelines.yml file."
                build.output      += "\n"
                build.status       = "FAILED"
                build.datetime_end = timezone.now()
                build.save(update_fields=["output", "status", "datetime_end"])

                # Build Status = FAILED
                service.set_build_status(build, "FAILED")

                return "FAILED"

            pipeline_yml = yaml.safe_load(open_pipelines_yml)
            if type(pipeline_yml) != dict:
                build.output      += "\n"
                build.output      += "ERROR: Failed to parse open_pipelines.yml file."
                build.output      += "\n"
                build.status       = "FAILED"
                build.datetime_end = timezone.now()
                build.save(update_fields=["output", "status", "datetime_end"])

                # Build Status = FAILED
                service.set_build_status(build, "FAILED")

                return "FAILED"

            pipeline_yml_image    = pipeline_yml.get("image")
            pipeline_yml_pipeline = pipeline_yml.get("pipeline")

            if any([type(pipeline_yml_image) != str, type(pipeline_yml_pipeline) != list]):
                build.output      += "\n"
                build.output      += "ERROR: Failed to parse open_pipelines.yml file."
                build.output      += "\n"
                build.status       = "FAILED"
                build.datetime_end = timezone.now()
                build.save(update_fields=["output", "status", "datetime_end"])

                # Build Status = FAILED
                service.set_build_status(build, "FAILED")

                return "FAILED"

            build.docker_image = pipeline_yml_image
            build.save(update_fields=["docker_image"])

            pipeline_SCRIPT, pipeline_SCRIPT_path = tempfile.mkstemp(
                prefix = "pipeline_",
                suffix = ".sh",
                dir    = pth_sh,
            )

            with open(pipeline_SCRIPT_path, "w") as f:
                f.write("umask 000")
                f.write("\n")

                for c in service.get_git_cmds(build):
                    f.write(c)
                    f.write("\n")

                f.write("chmod 777 $BUILD_DIR")
                f.write("\n")

                for c in pipeline_yml_pipeline:
                    f.write(c)
                    f.write("\n")

            docker_client    = docker.from_env()
            docker_container = docker_client.containers.run(
                image       = pipeline_yml_image,
                tty         = True,
                mem_limit   = "1G",
                detach      = True,
                working_dir = pth_ws,
                entrypoint  = ["/bin/bash", "-xe"],
                command     = pipeline_SCRIPT_path,
                environment = ["REPOSITORY_OAUTH_ACCESS_TOKEN={0}".format(oauth_atoken), "BUILD_DIR={0}".format(pth_ws)],
                volumes     = {
                    pth_ws               : {"bind" : pth_ws              , "mode" : "rw"},
                    pipeline_SCRIPT_path : {"bind" : pipeline_SCRIPT_path, "mode" : "ro"},
                },
            )

            tmp_buffer = ""
            for line in docker_container.logs(stream=True):
                tmp_buffer += line
                if tmp_buffer.count("\n") >= 10:
                    buff_index    = tmp_buffer.rfind("\n")
                    split_pos     = buff_index + 1

                    build_output  = tmp_buffer[:split_pos]
                    build_output  = build_output.replace(oauth_atoken, "$REPOSITORY_OAUTH_ACCESS_TOKEN")
                    build_output  = build_output.replace(pth_ws, "$BUILD_DIR")
                    build.output += build_output

                    tmp_buffer    = tmp_buffer[split_pos:]
                    build.save(update_fields=["output"])

            build_output  = tmp_buffer
            build_output  = build_output.replace(oauth_atoken, "$REPOSITORY_OAUTH_ACCESS_TOKEN")
            build_output  = build_output.replace(pth_ws, "$BUILD_DIR")
            build.output += build_output
            build.save(update_fields=["output"])

            docker_rcode = docker_container.wait()
            docker_container.remove()

            if docker_rcode != 0:
                # Build finished with errors
                build.status       = "FAILED"
                build.datetime_end = timezone.now()
                build.save(update_fields=["status", "datetime_end"])

                # Build Status = FAILED
                service.set_build_status(build, "FAILED")

                return "FAILED"

    except Exception as e:
        # Build finished with unexpected errors
        build.status       = "FAILED"
        build.datetime_end = timezone.now()
        build.save(update_fields=["status", "datetime_end"])

        # Build Status = FAILED
        service.set_build_status(build, "FAILED")

        return "FAILED Exception = {0}".format(e)

    # Build finished succesfully
    build.status       = "SUCCESSFUL"
    build.datetime_end = timezone.now()
    build.save(update_fields=["status", "datetime_end"])

    # Build Status = SUCCESSFUL
    service.set_build_status(build, "SUCCESSFUL")

    return "SUCCESSFUL"

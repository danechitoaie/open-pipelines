# System
from uuid import uuid4

# Django
from django.db         import models
from django.utils.text import Truncator


class User(models.Model):
    uuid             = models.UUIDField(default=uuid4, primary_key=True)
    username         = models.CharField(max_length=256, db_index=True)
    display_name     = models.CharField(max_length=256)
    service_id       = models.CharField(max_length=256)
    service_username = models.CharField(max_length=256)
    service_atoken   = models.CharField(max_length=256)
    service_rtoken   = models.CharField(max_length=256, null=True, blank=True)
    service_etoken   = models.DateTimeField(null=True, blank=True)
    last_login       = models.DateTimeField(auto_now_add=True)

    def is_repo_enabled(self, repo_path):
        try:
            repo = self.repo_set.get(path=repo_path)
            return repo.enabled
        except Repo.DoesNotExist:
            pass
        return False


class Repo(models.Model):
    uuid    = models.UUIDField(default=uuid4, primary_key=True)
    user    = models.ForeignKey(User)
    path    = models.CharField(max_length=256, db_index=True)
    enabled = models.BooleanField()
    public  = models.BooleanField()


class Build(models.Model):
    uuid                = models.UUIDField(default=uuid4, primary_key=True)
    repo                = models.ForeignKey(Repo)
    docker_image        = models.CharField(max_length=256, null=True, blank=True)
    ref                 = models.CharField(max_length=256)
    commit              = models.CharField(max_length=256)
    message             = models.CharField(max_length=256)
    author_username     = models.CharField(max_length=256)
    author_display_name = models.CharField(max_length=256)
    status              = models.CharField(max_length=256)
    output              = models.TextField()
    datetime_start      = models.DateTimeField(null=True, blank=True)
    datetime_end        = models.DateTimeField(null=True, blank=True)

    def get_build_steps(self, after=0):
        steps = []

        for step_body in self.output.split("\x1d"):
            step_title = Truncator(step_body[:step_body.find("\n")].rstrip()).chars(80)

            steps.append({
                "title" : step_title,
                "body"  : step_body
            })

        return steps[after:] if after > 0 else steps
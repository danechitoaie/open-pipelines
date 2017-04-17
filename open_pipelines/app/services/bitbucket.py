# System
import logging
import json

# System
from datetime     import timedelta
from urllib.parse import urlencode

# Django
from django.conf  import settings
from django.utils import timezone
from django.urls  import reverse

# Open Pipelines
from ..util import build_absolute_uri

# Requests
import requests


class BitBucketService(object):
    def __init__(self):
        self.l = logging.getLogger(__name__)

    def get_id(self):
        return "bitbucket"

    def get_display_name(self):
        return "BitBucket"

    def get_user_href(self, user):
        return "https://bitbucket.org/{0}/".format(user.service_username)

    def get_oauth_url(self):
        return "https://bitbucket.org/site/oauth2/authorize?" + urlencode({
            "client_id"     : settings.OPEN_PIPELINES_BITBUCKET_OAUTH_KEY,
            "response_type" : "code",
        })

    def process_oauth(self, oauth_code):
        try:
            token_req = requests.post(
                url  = "https://bitbucket.org/site/oauth2/access_token",
                data = {"grant_type" : "authorization_code", "code" : oauth_code},
                auth = (
                    settings.OPEN_PIPELINES_BITBUCKET_OAUTH_KEY,
                    settings.OPEN_PIPELINES_BITBUCKET_OAUTH_SECRET,
                )
            )
        except Exception as e:
            self.l.error(e)
            return None

        if not token_req.ok:
            self.l.error("Error requesting access_token from BitBucket! token_req=%s", token_req.text)
            return None

        try:
            token_req_json = token_req.json()
        except Exception as e:
            self.l.error(e)
            return None

        if type(token_req_json) != dict:
            self.l.error("Invalid JSON format! token_req_json=%s", repr(token_req_json))
            return None

        if any((
                token_req_json.get("access_token")  == None,
                token_req_json.get("refresh_token") == None,
                token_req_json.get("expires_in")    == None,
            )):
            self.l.error("Invalid JSON response! token_req_json=%s", repr(token_req_json))
            return None

        auth_atoken = token_req_json.get("access_token")
        auth_rtoken = token_req_json.get("refresh_token")
        auth_etoken = token_req_json.get("expires_in")

        try:
            user_req = requests.get(
                url     = "https://api.bitbucket.org/2.0/user",
                headers = {"Authorization" : "Bearer {0}".format(auth_atoken)}
            )
        except Exception as e:
            self.l.error(e)
            return None

        if not user_req.ok:
            self.l.error("Error requesting access_token from BitBucket! user_req=%s", user_req.text)
            return None

        try:
            user_req_json = user_req.json()
        except Exception as e:
            self.l.error(e)
            return None

        if type(user_req_json) != dict:
            self.l.error("Invalid JSON format! user_req_json=%s", repr(user_req_json))
            return None

        if user_req_json.get("username") == None:
            self.l.error("Invalid JSON response! user_req_json=%s", repr(user_req_json))
            return None

        auth_username     = user_req_json.get("username")
        auth_display_name = user_req_json.get("display_name") or ""

        return {
            "atoken"       : auth_atoken,
            "rtoken"       : auth_rtoken,
            "etoken"       : timezone.now() + timedelta(seconds=auth_etoken),
            "username"     : auth_username,
            "display_name" : auth_display_name,
        }

    def __refresh_oauth(self, user):
        if user.service_etoken > timezone.now() + timedelta(minutes=10):
            return True

        try:
            token_req = requests.post(
                url  = "https://bitbucket.org/site/oauth2/access_token",
                data = {"grant_type" : "refresh_token", "refresh_token" : user.service_rtoken},
                auth = (
                    settings.OPEN_PIPELINES_BITBUCKET_OAUTH_KEY,
                    settings.OPEN_PIPELINES_BITBUCKET_OAUTH_SECRET,
                )
            )
        except Exception as e:
            self.l.error(e)
            return False

        if not token_req.ok:
            self.l.error("Error requesting access_token from BitBucket! token_req=%s", token_req.text)
            return False

        try:
            token_req_json = token_req.json()
        except Exception as e:
            self.l.error(e)
            return False

        if type(token_req_json) != dict:
            self.l.error("Invalid JSON format! token_req_json=%s", repr(token_req_json))
            return False

        if any((
                token_req_json.get("access_token")  == None,
                token_req_json.get("refresh_token") == None,
                token_req_json.get("expires_in")    == None,
            )):
            self.l.error("Invalid JSON response! token_req_json=%s", repr(token_req_json))
            return False

        user.service_atoken = token_req_json.get("access_token")
        user.service_rtoken = token_req_json.get("refresh_token")
        user.service_etoken = timezone.now() + timedelta(seconds=token_req_json.get("expires_in"))
        user.save(update_fields=["service_atoken", "service_rtoken", "service_etoken"])
        return True

    def get_repos(self, user, page):
        self.__refresh_oauth(user)

        url_b = "https://api.bitbucket.org/2.0/repositories/{0}?".format(user.service_username)
        url_q = {"role" : "owner", "sort" : "-updated_on"}

        if page > 1:
            url_q["page"] = page

        try:
            repos_req = requests.get(
                url     = url_b + urlencode(url_q),
                headers = {"Authorization" : "Bearer {0}".format(user.service_atoken)}
            )
        except Exception as e:
            self.l.error(e)
            return None

        if not repos_req.ok:
            self.l.error("Error retrieving the list of repos from BitBucket! repos_req=%s", repos_req.text)
            return None

        try:
            repos_req_json = repos_req.json()
        except Exception as e:
            self.l.error(e)
            return None

        repos = [{
            "name"    : r.get("name"),
            "path"    : r.get("full_name"),
            "href"    : r.get("links").get("html").get("href"),
            "url"     : reverse("repo_by_path_json", args=[r.get("full_name")]),
            "enabled" : user.is_repo_enabled(r.get("full_name")),
        } for r in repos_req_json.get("values")]

        prev_href = None
        if "previous" in repos_req_json:
            try:
                prev_page = repos_req_json.get("page") - 1
                prev_href = reverse("repos_json") + "?" + urlencode({"p" : prev_page}) if prev_page > 1 else reverse("repos_json")
            except Exception as e:
                self.l.error(e)
                return None

        next_href = None
        if "next" in repos_req_json:
            try:
                next_page = repos_req_json.get("page") + 1
                next_href = reverse("repos_json") + "?" + urlencode({"p" : next_page})
            except Exception as e:
                self.l.error(e)
                return None

        return {
            "repos"     : repos,
            "prev_href" : prev_href,
            "next_href" : next_href,
        }

    def parse_webhook_request(self, payload):
        try:
            json_payload = json.loads(payload)
            repo_path    = json_payload.get("repository").get("full_name")
            changes      = []

            for change in json_payload.get("push").get("changes"):
                change_new = change.get("new")
                if change_new != None:
                    changes.append({
                        "ref"                 : change_new.get("name"),
                        "commit"              : change_new.get("target").get("hash"),
                        "message"             : change_new.get("target").get("message"),
                        "author_username"     : change_new.get("target").get("author").get("user").get("username"),
                        "author_display_name" : change_new.get("target").get("author").get("user").get("display_name"),
                    })
        except Exception as e:
            self.l.error(e)
            return None

        return {
            "repo_path" : repo_path,
            "changes"   : changes,
        }

    def set_build_status(self, build, status):
        repo = build.repo
        user = repo.user

        self.__refresh_oauth(user)

        build_statuses = {
            "INPROGRESS" : "INPROGRESS",
            "SUCCESSFUL" : "SUCCESSFUL",
            "FAILED"     : "FAILED",
        }

        if not status in build_statuses:
            self.l.error("Invalid build status! status=%s", status)
            return False

        url = "https://api.bitbucket.org/2.0/repositories/{0}/commit/{1}/statuses/build".format(
            repo.path, build.commit
        )

        try:
            req = requests.post(
                url     = url,
                headers = {"Authorization" : "Bearer {0}".format(user.service_atoken)},
                json    = {
                    "key"   : str(build.uuid),
                    "name"  : "OpenPipelines on {0}".format(build.ref),
                    "url"   : build_absolute_uri(reverse("build_by_uuid", args=[str(build.uuid)])),
                    "state" : build_statuses.get(status),
                }
            )
        except Exception as e:
            self.l.error(e)
            return False

        if not req.ok:
            self.l.error("Error updating build status on BitBucket! req=%s", req.text)
            return False

        return True

    def get_open_pipelines_yml(self, build):
        repo = build.repo
        user = repo.user

        self.__refresh_oauth(user)

        try:
            req = requests.get(
                url     = "https://api.bitbucket.org/1.0/repositories/{0}/raw/{1}/open_pipelines.yml".format(repo.path, build.commit),
                headers = {"Authorization" : "Bearer {0}".format(user.service_atoken)}
            )
        except Exception as e:
            self.l.error(e)
            return None

        if not req.ok:
            self.l.error("Error retrieving open_pipelines.yml from BitBucket! req=%s", req.text)
            return None

        return req.text

    def get_git_cmds(self, build):
        repo = build.repo
        user = repo.user

        self.__refresh_oauth(user)

        cmds = [
            "git clone --quiet https://x-token-auth:$REPOSITORY_OAUTH_ACCESS_TOKEN@bitbucket.org/{0}.git $BUILD_DIR".format(repo.path),
            "cd $BUILD_DIR",
            "git reset --hard {0}".format(build.commit),
            "git remote set-url origin git@bitbucket.org:{0}.git".format(repo.path),
        ]

        return cmds


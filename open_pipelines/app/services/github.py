# System
import logging
import json

# System
from datetime     import timedelta
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs

# Django
from django.conf  import settings
from django.utils import timezone
from django.urls  import reverse

# Open Pipelines
from ..util import build_absolute_uri

# Requests
import requests


class GitHubService(object):
    def __init__(self):
        self.l = logging.getLogger(__name__)

    def get_id(self):
        return "github"

    def get_display_name(self):
        return "GitHub"

    def get_user_href(self, user):
        return "https://github.com/{0}".format(user.service_username)

    def get_oauth_url(self):
        return "https://github.com/login/oauth/authorize?" + urlencode({
            "client_id" : settings.OPEN_PIPELINES_GITHUB_OAUTH_KEY,
            "scope"     : "repo repo:status admin:repo_hook",
        })

    def process_oauth(self, oauth_code):
        try:
            token_req = requests.post(
                url     = "https://github.com/login/oauth/access_token",
                headers = {"Accept" : "application/json"},
                data    = {
                    "client_id"     : settings.OPEN_PIPELINES_GITHUB_OAUTH_KEY,
                    "client_secret" : settings.OPEN_PIPELINES_GITHUB_OAUTH_SECRET,
                    "code"          : oauth_code,
                }
            )
        except Exception as e:
            self.l.error(e)
            return None

        if not token_req.ok:
            self.l.error("Error requesting access_token from GitHub! token_req=%s", token_req.text)
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
                token_req_json.get("scope")         == None,
            )):
            self.l.error("Invalid JSON response! token_req_json=%s", repr(token_req_json))
            return None

        auth_atoken = token_req_json.get("access_token")
        auth_scope  = token_req_json.get("scope")

        try:
            user_req = requests.get(
                url     = "https://api.github.com/user",
                headers = {
                    "Authorization" : "token {0}".format(auth_atoken),
                    "Accept"        : "application/vnd.github.v3+json",
                }
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

        if user_req_json.get("login") == None:
            self.l.error("Invalid JSON response! user_req_json=%s", repr(user_req_json))
            return None

        auth_username     = user_req_json.get("login")
        auth_display_name = user_req_json.get("name") or ""

        return {
            "atoken"       : auth_atoken,
            "rtoken"       : None,
            "etoken"       : None,
            "username"     : auth_username,
            "display_name" : auth_display_name,
        }

    def get_repos(self, user, page):
        url_b = "https://api.github.com/user/repos?"
        url_q = {"type" : "owner", "sort" : "updated", "direction" : "desc", "per_page": 20}

        if page > 1:
            url_q["page"] = page

        try:
            repos_req = requests.get(
                url     = url_b + urlencode(url_q),
                headers = {
                    "Authorization" : "token {0}".format(user.service_atoken),
                    "Accept"        : "application/vnd.github.v3+json",
                }
            )
        except Exception as e:
            self.l.error(e)
            return None

        if not repos_req.ok:
            self.l.error("Error retrieving the list of repos from GitHub! repos_req=%s", repos_req.text)
            return None

        try:
            repos_req_json = repos_req.json()
        except Exception as e:
            self.l.error(e)
            return None

        repos = [{
            "name"    : r.get("name"),
            "path"    : r.get("full_name"),
            "href"    : r.get("html_url"),
            "url"     : reverse("repo_by_path_json", args=[r.get("full_name")]),
            "enabled" : user.is_repo_enabled(r.get("full_name")),
        } for r in repos_req_json]

        prev_href = None
        if "prev" in repos_req.links:
            try:
                prev_purl = urlparse(repos_req.links.get("prev").get("url"))
                prev_qstr = parse_qs(prev_purl.query)
                if "page" in prev_qstr and len(prev_qstr.get("page")) > 0:
                    prev_page = int(prev_qstr.get("page")[0])
                    prev_href = reverse("repos_json") + "?" + urlencode({"p" : prev_page}) if prev_page > 1 else reverse("repos_json")
                else:
                    prev_href = reverse("repos_json")
            except Exception as e:
                self.l.error(e)
                return None

        next_href = None
        if "next" in repos_req.links:
            try:
                next_purl = urlparse(repos_req.links.get("next").get("url"))
                next_qstr = parse_qs(next_purl.query)
                if "page" in next_qstr and len(next_qstr.get("page")) > 0:
                    next_page = int(next_qstr.get("page")[0])
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
            changes      = [{
                "ref"                 : json_payload.get("ref"),
                "commit"              : json_payload.get("head_commit").get("id"),
                "message"             : json_payload.get("head_commit").get("message"),
                "author_username"     : json_payload.get("head_commit").get("author").get("username"),
                "author_display_name" : json_payload.get("head_commit").get("author").get("name"),
            }]

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

        build_statuses = {
            "INPROGRESS" : "pending",
            "SUCCESSFUL" : "success",
            "FAILED"     : "failure",
        }

        if not status in build_statuses:
            self.l.error("Invalid build status! status=%s", status)
            return False

        url = "https://api.github.com/repos/{0}/statuses/{1}".format(
            repo.path, build.commit
        )

        try:
            req = requests.post(
                url     = url,
                headers = {
                    "Authorization" : "token {0}".format(user.service_atoken),
                    "Accept"        : "application/vnd.github.v3+json",
                },
                json    = {
                    "state"       : build_statuses.get(status),
                    "target_url"  : build_absolute_uri(reverse("build_by_uuid", args=[str(build.uuid)])),
                    "description" : "OpenPipelines on {0}".format(build.ref),
                    "context"     : "continuous-integration/open-pipelines",
                }
            )
        except Exception as e:
            self.l.error(e)
            return False

        if not req.ok:
            self.l.error("Error updating build status on BitBucket! req=%s", req.text)
            return False

        return True

    def get_git_cmds(self, build):
        repo = build.repo
        cmds = [
            "git clone https://$REPOSITORY_OAUTH_ACCESS_TOKEN:x-oauth-basic@github.com/{0}.git .".format(repo.path),
            "git reset --hard {0}".format(build.commit),
            "git remote set-url origin git@github.com:{0}.git".format(repo.path),
        ]

        return cmds

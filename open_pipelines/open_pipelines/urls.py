"""open_pipelines URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls  import url
from app.views.index   import IndexView
from app.views.repos   import ReposJsonView
from app.views.repos   import RepoByPathJsonView
from app.views.builds  import BuildByUUIDView
from app.views.builds  import BuildByUUIDJsonView
from app.views.webhook import WebhookByUUIDView
from app.views.login   import LoginView
from app.views.login   import LoginWithServiceView
from app.views.logout  import LogoutView

urlpatterns = [
    # Index
    url(r'^$',
        view = IndexView.as_view(),
        name = "index"
    ),

    # Repos
    url(r'^repos\.json$',
        view = ReposJsonView.as_view(),
        name = "repos_json"
    ),

    # Repo by Path
    url(r'^repos\/(.+)\.json$',
        view = RepoByPathJsonView.as_view(),
        name = "repo_by_path_json"
    ),

    # Build by UUID
    url(r'^builds\/([0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12})$',
        view = BuildByUUIDView.as_view(),
        name = "build_by_uuid"
    ),

    # Build by UUID JSON
    url(r'^builds\/([0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12})\.json$',
        view = BuildByUUIDJsonView.as_view(),
        name = "build_by_uuid_json"
    ),

    # Webhook
    url(r'^webhook\/([0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12})$',
        view = WebhookByUUIDView.as_view(),
        name = "webhook_by_uuid"
    ),

    # Login
    url(r'^login$',
        view = LoginView.as_view(),
        name = "login"
    ),

    # Login - With Service
    url(r'^login\/(.+)$',
        view = LoginWithServiceView.as_view(),
        name = "login_with_service"
    ),

    # Logout
    url(r'^logout$',
        view = LogoutView.as_view(),
        name = "logout"
    ),
]

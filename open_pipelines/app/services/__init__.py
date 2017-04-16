# Services
from .bitbucket import BitBucketService
from .github    import GitHubService


class ServiceManager(object):
    class DoesNotExist(Exception):
        pass

    def __init__(self):
        self.services = [
            BitBucketService(),
            GitHubService(),
        ]

    def get_service(self, service_id):
        for service in self.services:
            if hasattr(service, "get_id") and service.get_id() == service_id:
                return service
        raise self.DoesNotExist("Unknown service!")

    def get_services(self):
        return self.services

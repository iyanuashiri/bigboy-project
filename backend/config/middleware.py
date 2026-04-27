"""Request tweaks for platforms that probe with non-public Host headers."""


class AppRunnerLinkLocalHostMiddleware:
    """
    App Runner health checks hit the container with Host in the 169.254.0.0/16 link-local
    range (e.g. 169.254.172.2:8000), not the public *.awsapprunner.com hostname. Django
    would raise DisallowedHost. Rewrite to localhost for this request only.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get("HTTP_HOST", "")
        if host:
            hostname = host.split(":")[0]
            if hostname.startswith("169.254."):
                request.META["HTTP_HOST"] = "localhost"
        return self.get_response(request)

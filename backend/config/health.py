"""Liveness probe for load balancers / App Runner (no DB, no DRF schema work)."""

from django.http import HttpResponse


def healthz(_request):
    return HttpResponse("ok", content_type="text/plain")

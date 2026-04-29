"""Boto3 / LangChain Bedrock kwargs from Django settings (IAM when keys unset)."""

from __future__ import annotations

from typing import Any

from django.conf import settings


def aws_boto_client_kwargs() -> dict[str, Any]:
    """region_name plus optional static credentials; omit empty keys for default credential chain."""
    kw: dict[str, Any] = {'region_name': settings.AWS_REGION_NAME}
    ak = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    sk = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
    if ak:
        kw['aws_access_key_id'] = ak
    if sk:
        kw['aws_secret_access_key'] = sk
    return kw

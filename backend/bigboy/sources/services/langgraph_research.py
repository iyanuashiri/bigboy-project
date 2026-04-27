"""Call the standalone LangGraph research HTTP service."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def invoke_research_agent(*, query: str, thread_id: str | None) -> dict[str, Any]:
    """
    POST /v1/research/run on langgraph-service.

    Returns a dict with: ok (bool), thread_id, status, result_blocks (list), error_message (str).
    """
    base = (getattr(settings, 'LANGGRAPH_SERVICE_URL', None) or '').strip().rstrip('/')
    if not base:
        return {
            'ok': False,
            'thread_id': thread_id or '',
            'status': 'failed',
            'result_blocks': [],
            'error_message': 'LANGGRAPH_SERVICE_URL is not set.',
        }

    url = f'{base}/v1/research/run'
    headers: dict[str, str] = {'Content-Type': 'application/json'}
    api_key = (getattr(settings, 'LANGGRAPH_SERVICE_API_KEY', None) or '').strip()
    if api_key:
        headers['X-Research-Service-Key'] = api_key

    timeout = float(getattr(settings, 'LANGGRAPH_SERVICE_TIMEOUT', 120) or 120)
    payload = {'query': query, 'thread_id': thread_id}

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        logger.exception('LangGraph service request failed')
        return {
            'ok': False,
            'thread_id': thread_id or '',
            'status': 'failed',
            'result_blocks': [],
            'error_message': f'{type(exc).__name__}: {exc}',
        }

    try:
        body = response.json() if response.content else {}
    except ValueError:
        body = {'detail': response.text[:2000]}

    if response.status_code >= 400:
        detail = body.get('detail')
        if isinstance(detail, list):
            msg = ', '.join(str(x) for x in detail)
        else:
            msg = str(detail or response.text or response.reason_phrase)
        return {
            'ok': False,
            'thread_id': thread_id or '',
            'status': 'failed',
            'result_blocks': [],
            'error_message': f'HTTP {response.status_code}: {msg}'[:10000],
        }

    blocks = body.get('result_blocks') or []
    if not isinstance(blocks, list):
        blocks = []
    normalized = []
    for item in blocks:
        if isinstance(item, dict):
            normalized.append(
                {
                    'title': str(item.get('title', 'Section'))[:500],
                    'body': str(item.get('body', '')),
                }
            )

    status = str(body.get('status') or 'failed')
    err = body.get('error_message')
    err_str = str(err).strip() if err else ''
    ok = status == 'succeeded' and not err_str

    return {
        'ok': ok,
        'thread_id': str(body.get('thread_id') or thread_id or ''),
        'status': status,
        'result_blocks': normalized,
        'error_message': err_str[:10000],
    }

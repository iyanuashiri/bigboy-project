from __future__ import annotations

import logging

from celery import shared_task

from bigboy.sources.models import SourceDocument
from bigboy.sources.services.rag import index_source_document

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
def index_source_document_task(self, document_id: int) -> dict:
    try:
        doc = SourceDocument.objects.get(pk=document_id)
    except SourceDocument.DoesNotExist:
        logger.warning("index_source_document_task: document %s does not exist", document_id)
        return {"document_id": document_id, "status": "missing"}

    if doc.status != SourceDocument.ProcessingStatus.PROCESSING:
        doc.status = SourceDocument.ProcessingStatus.PROCESSING
        doc.processing_error = ''
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])

    index_source_document(doc)
    doc.refresh_from_db()
    return {"document_id": doc.id, "status": doc.status}

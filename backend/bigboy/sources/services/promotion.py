"""Promote neutral source rows into curriculum objects (subjects today; extensible later)."""

from __future__ import annotations

from typing import Optional, Tuple

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction

from bigboy.sources.models import (
    DocumentCategory,
    McpConversationImport,
    ResearchRun,
    SourcePromotion,
)
from bigboy.sources.services.promotion_curriculum import materialize_topics_and_bites
from bigboy.subjects.models import Enrollment, Subject

SOURCE_MODEL_SLUGS = {
    'documentcategory': DocumentCategory,
    'researchrun': ResearchRun,
    'mcpconversationimport': McpConversationImport,
}


def resolve_source_model(slug: str):
    key = (slug or '').strip().lower()
    return SOURCE_MODEL_SLUGS.get(key)


@transaction.atomic
def promote_to_subject(
    *,
    account,
    source_model_slug: str,
    source_id: int,
    subject_name: str,
    subject_description: str,
) -> Tuple[Optional[Subject], Optional[SourcePromotion], Optional[str]]:
    """
    Create a Subject, enroll the account, and record SourcePromotion (completed).

    Returns (subject, promotion, error_message). On success error_message is None.
    On recoverable validation errors returns (None, None, "reason").
    On IntegrityError for duplicate promotion returns (None, None, "...").
    """
    model = resolve_source_model(source_model_slug)
    if not model:
        return None, None, f'Unknown source model: {source_model_slug!r}'

    source = model.objects.filter(pk=source_id, account=account).first()
    if not source:
        return None, None, 'Source not found or not owned by this user.'

    subject = Subject.objects.create_subject_by_user(
        name=subject_name[:100],
        description=subject_description,
    )
    Enrollment.objects.get_or_create(account=account, subject=subject)

    try:
        materialize_topics_and_bites(subject, source=source, source_model_slug=source_model_slug)
    except Exception as exc:  # noqa: BLE001
        transaction.set_rollback(True)
        return None, None, f'Could not build topics/bites from source: {exc}'

    ct_source = ContentType.objects.get_for_model(source)
    ct_target = ContentType.objects.get_for_model(subject)

    try:
        promotion = SourcePromotion.objects.create(
            account=account,
            source_content_type=ct_source,
            source_object_id=source.pk,
            target_content_type=ct_target,
            target_object_id=subject.pk,
            status=SourcePromotion.Status.COMPLETED,
        )
    except IntegrityError:
        transaction.set_rollback(True)
        return None, None, 'This source was already promoted to this subject (duplicate link).'

    return subject, promotion, None

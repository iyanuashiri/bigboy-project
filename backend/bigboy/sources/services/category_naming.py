"""LLM-generated titles for document categories (bounded text, no full-corpus load)."""

from __future__ import annotations

import logging
import re

from decouple import config
from django.db import transaction
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate

from bigboy.sources.models import DocumentCategory
from bigboy.sources.schemas_category import DocumentCategoryLabelSchema

logger = logging.getLogger(__name__)

_MAX_SAMPLE_CHARS = 6_000
_MAX_NAMES_LIST = 12


def _bedrock_llm() -> ChatBedrock:
    return ChatBedrock(
        model_id=config('BEDROCK_MODEL_ID', default='global.amazon.nova-2-lite-v1:0'),
        region_name=config('AWS_REGION_NAME', default='us-east-2'),
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
    )


def _clean_title(name: str) -> str:
    s = re.sub(r'\s+', ' ', (name or '').strip())
    return s[:200] if s else ''


def suggest_category_label(
    *,
    text_sample: str,
    document_filenames: list[str],
    user_hint: str = '',
) -> DocumentCategoryLabelSchema | None:
    """Single Bedrock call; `text_sample` must already be truncated."""
    sample = (text_sample or '').strip()
    if len(sample) < 80:
        return None

    names = [n for n in document_filenames if n][: _MAX_NAMES_LIST]
    names_block = '\n'.join(f'- {n}' for n in names) if names else '(no filenames)'

    hint = (user_hint or '').strip()
    hint_block = f'Optional user note about this collection:\n{hint}\n\n' if hint else ''

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                'You name a small document library in a learning app.\n'
                'Infer a clear category title and description from the excerpt and file names only.\n'
                'Do not claim to have read entire files. Stay grounded in what the excerpt suggests.',
            ),
            (
                'human',
                'File names:\n{names_block}\n\n'
                '{hint_block}'
                'Beginning of extracted text (may be truncated):\n---\n{sample}\n---',
            ),
        ]
    )

    llm = _bedrock_llm()
    chain = prompt | llm.with_structured_output(DocumentCategoryLabelSchema)
    return chain.invoke(
        {
            'names_block': names_block,
            'hint_block': hint_block,
            'sample': sample[:_MAX_SAMPLE_CHARS],
        }
    )


def try_autoname_category_after_index(
    *,
    category_id: int,
    text_head: str,
    document_filenames: list[str],
) -> None:
    """
    If this category has not been auto-labeled yet, run one small LLM call and update name/description.

    Uses only `text_head` (bounded) plus filenames — not every page of every upload.
    LLM runs outside a DB lock; a conditional update avoids clobbering another worker's result.
    """
    if not DocumentCategory.objects.filter(pk=category_id, auto_label_completed=False).exists():
        return

    row = DocumentCategory.objects.filter(pk=category_id).values('description').first()
    user_hint = (row or {}).get('description') or ''

    try:
        result = suggest_category_label(
            text_sample=text_head[:_MAX_SAMPLE_CHARS],
            document_filenames=document_filenames,
            user_hint=str(user_hint),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning('Category auto-label LLM failed for category %s: %s', category_id, exc)
        return

    if not result:
        return

    name = _clean_title(result.name)
    desc = (result.description or '').strip()
    if not name:
        return

    new_description = desc[:5000] if desc else str(user_hint)[:5000]

    with transaction.atomic():
        updated = DocumentCategory.objects.filter(
            pk=category_id,
            auto_label_completed=False,
        ).update(
            name=name[:200],
            description=new_description,
            auto_label_completed=True,
        )

    if not updated:
        logger.debug('Category %s auto-label skipped (already completed).', category_id)

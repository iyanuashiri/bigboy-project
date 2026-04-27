"""Build Topic payloads when promoting Explore sources into Subjects."""

from __future__ import annotations

import logging
from typing import Any

from bigboy.sources.models import (
    DocumentCategory,
    DocumentChunk,
    McpConversationImport,
    ResearchRun,
    SourceDocument,
)
from bigboy.sources.services.rag import read_source_document_plaintext
from bigboy.subjects.models import Subject, Topic
from bigboy.subjects.prompts import generate_curriculum_topics

logger = logging.getLogger(__name__)

# Bedrock context size guard
_MAX_TOPIC_CONTENT_CHARS = 120_000
_MAX_CURRICULUM_SOURCE_CHARS = 95_000
_MIN_CHARS_FOR_LLM_CURRICULUM = 800

_QUESTIONS_PER_TOPIC = 5
_OPTIONS_PER_QUESTION = 4


def _truncate(s: str, n: int) -> str:
    s = (s or '').strip()
    if len(s) <= n:
        return s
    return s[: n - 1] + '…'


def topic_payloads_from_document_category(category: DocumentCategory) -> list[dict[str, str]]:
    """One topic per document with usable text; fallback to a single overview topic."""
    payloads: list[dict[str, str]] = []
    for doc in category.documents.order_by('id'):
        text = ''
        if doc.status == SourceDocument.ProcessingStatus.INDEXED:
            parts = [
                c.text
                for c in DocumentChunk.objects.filter(source_document=doc).order_by('chunk_index')
                if c.text
            ]
            text = '\n\n'.join(parts).strip()
        if not text and doc.stored_path:
            text = read_source_document_plaintext(doc).strip()
        if text:
            payloads.append(
                {
                    'name': _truncate(doc.original_name or 'Document', 100),
                    'description': _truncate(
                        f'Material from document in «{category.name}».',
                        500,
                    ),
                    'content': _truncate(text, _MAX_TOPIC_CONTENT_CHARS),
                }
            )

    intro = _truncate(f'# {category.name}\n\n{(category.description or "").strip()}', _MAX_TOPIC_CONTENT_CHARS)
    if not payloads:
        if intro.strip():
            payloads.append(
                {
                    'name': _truncate(category.name, 100),
                    'description': _truncate(category.description or 'Promoted from Explore', 500),
                    'content': intro,
                }
            )
        else:
            payloads.append(
                {
                    'name': _truncate(category.name, 100),
                    'description': 'Promoted from Explore',
                    'content': _truncate(
                        'No indexed documents or extractable files were found for this category. '
                        'Add text or PDF uploads, wait for indexing, then create a new subject or edit topics in Django admin.',
                        _MAX_TOPIC_CONTENT_CHARS,
                    ),
                }
            )
    return payloads


def topic_payloads_from_research_run(run: ResearchRun) -> list[dict[str, str]]:
    parts: list[str] = []
    for block in run.result_blocks or []:
        if isinstance(block, dict):
            title = str(block.get('title', '')).strip()
            body = str(block.get('body', '')).strip()
            if title or body:
                parts.append(f'## {title}\n{body}'.strip())
    body = '\n\n'.join(parts).strip() or (run.query or '').strip()
    return [
        {
            'name': _truncate(f'Research: {run.query[:80]}', 100),
            'description': _truncate('Generated from a research run.', 500),
            'content': _truncate(body, _MAX_TOPIC_CONTENT_CHARS),
        }
    ]


def topic_payloads_from_mcp_import(im: McpConversationImport) -> list[dict[str, str]]:
    text = (im.transcript or '').strip()
    if not text and im.raw_payload:
        text = str(im.raw_payload)[:_MAX_TOPIC_CONTENT_CHARS]
    return [
        {
            'name': _truncate(im.title or 'Conversation', 100),
            'description': _truncate(im.client_label or 'Imported conversation', 500),
            'content': _truncate(text or '(empty transcript)', _MAX_TOPIC_CONTENT_CHARS),
        }
    ]


def topic_payloads_for_promotion(*, source: Any, source_model_slug: str) -> list[dict[str, str]]:
    key = (source_model_slug or '').strip().lower()
    if key == 'documentcategory' and isinstance(source, DocumentCategory):
        return topic_payloads_from_document_category(source)
    if key == 'researchrun' and isinstance(source, ResearchRun):
        return topic_payloads_from_research_run(source)
    if key == 'mcpconversationimport' and isinstance(source, McpConversationImport):
        return topic_payloads_from_mcp_import(source)
    return []


def _payloads_unified_text(payloads: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for i, p in enumerate(payloads):
        title = (p.get('name') or f'Section {i + 1}').strip()
        body = (p.get('content') or '').strip()
        if body:
            parts.append(f'## {title}\n\n{body}')
    return '\n\n---\n\n'.join(parts).strip()


def _planned_rows_from_llm(
    *,
    unified_source: str,
    subject: Subject,
) -> list[dict[str, str]] | None:
    if len(unified_source.strip()) < _MIN_CHARS_FOR_LLM_CURRICULUM:
        return None
    trimmed = _truncate(unified_source, _MAX_CURRICULUM_SOURCE_CHARS)
    try:
        outline = generate_curriculum_topics(trimmed, context_title=subject.name)
    except Exception as exc:  # noqa: BLE001
        logger.warning('Curriculum topic split failed: %s', exc)
        return None
    rows: list[dict[str, str]] = []
    for t in outline.topics:
        name = _truncate((t.name or '').strip(), 100)
        desc = _truncate((t.description or '').strip(), 500)
        content = _truncate((t.content or '').strip(), _MAX_TOPIC_CONTENT_CHARS)
        if not name or not content:
            continue
        rows.append({'name': name, 'description': desc, 'content': content})
    if len(rows) >= 2:
        return rows
    return None


def _create_quiz_for_topic(subject: Subject, topic: Topic) -> None:
    from bigboy.quizzes.models import Quiz

    try:
        quiz = Quiz.objects.create(
            subject=subject,
            topic=topic,
            number_of_questions=_QUESTIONS_PER_TOPIC,
            number_of_options=_OPTIONS_PER_QUESTION,
        )
        quiz.generate_questions()
    except Exception as exc:  # noqa: BLE001
        logger.warning('Quiz generation failed for topic %s: %s', topic.pk, exc)


def materialize_topics_and_bites(subject: Subject, *, source: Any, source_model_slug: str) -> int:
    """
    Create Topic rows under `subject`, generate bites per topic, and create a quiz per topic.

    When source is long enough, an LLM first splits material into multiple topics; otherwise
    legacy per-document / single-blob payloads are used.

    Returns the number of topics created.
    """
    payloads = topic_payloads_for_promotion(source=source, source_model_slug=source_model_slug)
    unified = _payloads_unified_text(payloads)
    planned = _planned_rows_from_llm(unified_source=unified, subject=subject)
    rows = planned if planned is not None else payloads

    count = 0
    for p in rows:
        topic = Topic.objects.create(
            subject=subject,
            name=p['name'][:100],
            description=p.get('description') or '',
            content=p.get('content') or '',
        )
        topic.generate_bites()
        _create_quiz_for_topic(subject, topic)
        count += 1
    return count

"""RAG: index source documents and answer category chat with Bedrock + stored embeddings."""

from __future__ import annotations

import io
import logging
import math

from decouple import config
from django.core.files.storage import default_storage
from django.db import transaction
from langchain_aws import BedrockEmbeddings, ChatBedrock
from pypdf import PdfReader

from bigboy.sources.models import DocumentChunk, DocumentChatMessage, DocumentChatSession, SourceDocument
from bigboy.sources.services.category_naming import try_autoname_category_after_index

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
TOP_K = 8
MAX_HISTORY_CHARS = 6000


def _bedrock_embeddings() -> BedrockEmbeddings:
    model_id = config('BEDROCK_EMBEDDING_MODEL_ID', default='amazon.titan-embed-text-v2:0')
    return BedrockEmbeddings(
        model_id=model_id,
        region_name=config('AWS_REGION_NAME', default='us-east-2'),
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
    )


def _chat_bedrock() -> ChatBedrock:
    model_id = config('BEDROCK_MODEL_ID', default='global.amazon.nova-2-lite-v1:0')
    return ChatBedrock(
        model_id=model_id,
        region_name=config('AWS_REGION_NAME', default='us-east-2'),
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
    )


def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = (text or '').strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


def read_source_document_plaintext(doc: SourceDocument) -> str:
    """Read `stored_path` from default storage and return extractable text (used when promoting categories)."""
    if not doc.stored_path:
        return ''
    try:
        with default_storage.open(doc.stored_path, 'rb') as fh:
            raw = fh.read()
    except OSError:
        return ''
    return _extract_text_from_bytes(raw, doc.mime_type or '', doc.original_name)


def _extract_text_from_bytes(raw: bytes, mime_type: str, original_name: str) -> str:
    name = (original_name or '').lower()
    mt = (mime_type or '').lower()
    if name.endswith('.pdf') or 'pdf' in mt:
        reader = PdfReader(io.BytesIO(raw))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ''
            if t.strip():
                parts.append(t)
        return '\n\n'.join(parts).strip()
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('utf-8', errors='replace').strip()


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    a, b = a[:n], b[:n]
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def delete_chunks_for_document(doc: SourceDocument) -> None:
    DocumentChunk.objects.filter(source_document=doc).delete()


def index_source_document(doc: SourceDocument) -> None:
    """Read stored file, chunk, embed, replace chunks; updates document status."""
    if not doc.stored_path:
        doc.status = SourceDocument.ProcessingStatus.FAILED
        doc.processing_error = 'No stored_path; upload the file via multipart to index.'
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])
        return

    try:
        with default_storage.open(doc.stored_path, 'rb') as fh:
            raw = fh.read()
    except OSError as exc:
        doc.status = SourceDocument.ProcessingStatus.FAILED
        doc.processing_error = f'Could not read file: {exc}'
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])
        return

    text = _extract_text_from_bytes(raw, doc.mime_type or '', doc.original_name)
    if not text.strip():
        doc.status = SourceDocument.ProcessingStatus.FAILED
        doc.processing_error = 'No extractable text (empty PDF or binary file).'
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])
        return

    pieces = _split_text(text)
    if not pieces:
        doc.status = SourceDocument.ProcessingStatus.FAILED
        doc.processing_error = 'Chunking produced no segments.'
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])
        return

    embedder = _bedrock_embeddings()
    vectors = embedder.embed_documents(pieces)
    if len(vectors) != len(pieces):
        doc.status = SourceDocument.ProcessingStatus.FAILED
        doc.processing_error = f'Embedding count mismatch ({len(vectors)} vs {len(pieces)}).'
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])
        return

    with transaction.atomic():
        delete_chunks_for_document(doc)
        DocumentChunk.objects.bulk_create(
            [
                DocumentChunk(
                    source_document=doc,
                    chunk_index=i,
                    text=piece[:50000],
                    embedding=list(vectors[i]) if i < len(vectors) else [],
                )
                for i, piece in enumerate(pieces)
            ]
        )
        doc.status = SourceDocument.ProcessingStatus.INDEXED
        doc.processing_error = ''
        doc.save(update_fields=['status', 'processing_error', 'updated_at'])

        indexed_names = list(
            SourceDocument.objects.filter(
                category_id=doc.category_id,
                status=SourceDocument.ProcessingStatus.INDEXED,
            )
            .order_by('id')
            .values_list('original_name', flat=True)
        )
        try_autoname_category_after_index(
            category_id=doc.category_id,
            text_head=text[:6000],
            document_filenames=list(indexed_names),
        )


def _retrieve_context(*, category_id: int, query: str) -> tuple[str, list[dict]]:
    embedder = _bedrock_embeddings()
    qvec = embedder.embed_query(query)

    rows = list(
        DocumentChunk.objects.filter(source_document__category_id=category_id).select_related('source_document')
    )
    if not rows:
        return '', []

    scored: list[tuple[float, DocumentChunk]] = []
    for row in rows:
        emb = row.embedding or []
        if not emb:
            continue
        scored.append((_cosine(qvec, emb), row))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:TOP_K]

    blocks: list[str] = []
    citations: list[dict] = []
    for score, chunk in top:
        if score <= 0:
            continue
        doc = chunk.source_document
        header = f"[{doc.original_name} · segment {chunk.chunk_index}]"
        blocks.append(f'{header}\n{chunk.text}')
        citations.append(
            {
                'document_id': doc.id,
                'document_name': doc.original_name,
                'chunk_index': chunk.chunk_index,
                'score': round(score, 4),
            }
        )

    context = '\n\n---\n\n'.join(blocks)
    return context, citations


def _history_block(session: DocumentChatSession, exclude_message_id: int | None) -> str:
    qs = DocumentChatMessage.objects.filter(session=session).order_by('created_at', 'id')
    if exclude_message_id:
        qs = qs.exclude(pk=exclude_message_id)
    parts: list[str] = []
    for m in qs:
        content = (m.content or '').strip()
        if not content:
            continue
        parts.append(f'{m.role.upper()}: {content}')
    blob = '\n'.join(parts)
    if len(blob) > MAX_HISTORY_CHARS:
        blob = blob[-MAX_HISTORY_CHARS:]
    return blob


def rag_reply_for_session(*, session: DocumentChatSession, user_message: DocumentChatMessage) -> tuple[str, dict]:
    """
    Return (assistant_markdown_or_plain, metadata dict with citations / flags).
    """
    category_id = session.category_id
    q = (user_message.content or '').strip()
    context, citations = _retrieve_context(category_id=category_id, query=q)
    history = _history_block(session, exclude_message_id=user_message.pk)

    if not context.strip():
        return (
            'There is no indexed text for this category yet. Upload documents using the category form '
            '(file upload), wait until status is **indexed**, then ask again.',
            {'citations': [], 'rag': True, 'empty_corpus': True},
        )

    system = (
        'You are a helpful assistant answering questions using ONLY the CONTEXT below. '
        'If the answer is not in the context, say you do not have that information in the uploaded documents. '
        'Quote or paraphrase the context; mention document names when relevant. '
        'Be concise.'
    )
    user_block = (
        f'CONVERSATION SO FAR (most recent last):\n{history or "(no prior turns)"}\n\n'
        f'CONTEXT FROM DOCUMENTS:\n{context}\n\n'
        f'USER QUESTION:\n{q}'
    )

    llm = _chat_bedrock()
    out = llm.invoke(
        [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_block},
        ]
    )
    text = (out.content or '').strip()
    meta = {'citations': citations, 'rag': True, 'empty_corpus': False}
    return text, meta

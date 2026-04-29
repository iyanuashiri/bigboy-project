"""Generate a short 'why' explanation when a quiz answer is wrong (Bedrock, bounded context)."""

from __future__ import annotations

import logging

from django.conf import settings
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config.bedrock_client import aws_boto_client_kwargs

logger = logging.getLogger(__name__)


class WhyWrongSchema(BaseModel):
    explanation: str = Field(
        description='2–4 sentences: why the chosen answer is wrong and why the correct answer fits, '
        'using only the topic excerpt.',
    )


def _llm() -> ChatBedrock:
    return ChatBedrock(
        model_id=settings.BEDROCK_MODEL_ID,
        **aws_boto_client_kwargs(),
    )


def explain_wrong_answer(
    *,
    question_text: str,
    chosen_option: str,
    correct_option: str,
    topic_excerpt: str,
) -> str | None:
    excerpt = (topic_excerpt or '').strip()[:3500]
    if not question_text.strip():
        return None
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                'You help learners understand mistakes. Be concise, encouraging, and faithful to the excerpt. '
                'Do not invent facts beyond the excerpt.',
            ),
            (
                'human',
                'Question:\n{q}\n\n'
                'Learner chose:\n{wrong}\n\n'
                'Correct option:\n{right}\n\n'
                'Topic excerpt (may be truncated):\n---\n{excerpt}\n---',
            ),
        ]
    )
    try:
        chain = prompt | _llm().with_structured_output(WhyWrongSchema)
        out = chain.invoke(
            {
                'q': question_text.strip(),
                'wrong': (chosen_option or '').strip(),
                'right': (correct_option or '').strip(),
                'excerpt': excerpt or '(no excerpt)',
            },
        )
        return (out.explanation or '').strip() or None
    except Exception as exc:  # noqa: BLE001
        logger.warning('explain_wrong_answer failed: %s', exc)
        return None

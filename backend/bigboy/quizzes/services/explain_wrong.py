"""Generate a short 'why' explanation when a quiz answer is wrong (Bedrock, bounded context)."""

from __future__ import annotations

import logging

from decouple import config
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WhyWrongSchema(BaseModel):
    explanation: str = Field(
        description='2–4 sentences: why the chosen answer is wrong and why the correct answer fits, '
        'using only the topic excerpt.',
    )


def _llm() -> ChatBedrock:
    return ChatBedrock(
        model_id=config('BEDROCK_MODEL_ID', default='global.amazon.nova-2-lite-v1:0'),
        region_name=config('AWS_REGION_NAME', default='us-east-2'),
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
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

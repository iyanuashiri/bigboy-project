from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock

from config.bedrock_client import aws_boto_client_kwargs

from bigboy.subjects.schemas import (
    CurriculumOutlineSchema,
    InstructionalBitesSchema,
    PreferencesSchema,
)


def _bedrock_llm():
    return ChatBedrock(
        model_id=settings.BEDROCK_MODEL_ID,
        **aws_boto_client_kwargs(),
    )


def generate_bites(topic: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """You are an expert instructional designer.

Task: Split the topic material into ordered "bites" — the smallest *meaningful* units a learner can retain.

Rules:
- Each bite is a coherent idea (definition, mechanism, equation, comparison, limitation, example, etc.).
- NOT table-of-contents lines, NOT bare chapter titles, NOT single words.
- Each bite has a short title (2–6 words) and body text of one to four short paragraphs when needed.
- Ground every bite in the provided material; you may paraphrase tightly but do not invent unrelated facts.
- Order bites the way a learner should read them.""",
            ),
            ('human', 'Topic material:\n{topic}'),
        ]
    )

    llm = _bedrock_llm()
    structured_llm = llm.with_structured_output(InstructionalBitesSchema)
    chain = prompt | structured_llm
    return chain.invoke({'topic': topic})


def generate_curriculum_topics(source_material: str, context_title: str = '') -> CurriculumOutlineSchema:
    """Split long source text into multiple planned topics for a subject."""
    hint = (context_title or '').strip()
    approx = max(3, min(12, len(source_material) // 4500 + 2))

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """You design curricula from raw learning material.

Given source text, propose several distinct *topics* a course should contain.

Requirements:
- Each topic must have a clear scope (no duplicate coverage across topics).
- `content` for each topic must contain the actual teaching material for that topic drawn from the source
  (excerpts and/or tight, faithful paraphrase). It must be detailed enough that another model can write bites and quizzes from it alone.
- Order topics in a sensible learning sequence.
- If the source is shallow, still produce the minimum number of separate angles you honestly see.""",
            ),
            (
                'human',
                'Subject / context title: {hint}\n\n'
                'Aim for roughly {approx} topics (flexible if the source demands fewer or slightly more).\n\n'
                'Source material:\n{source_material}',
            ),
        ]
    )

    llm = _bedrock_llm()
    structured_llm = llm.with_structured_output(CurriculumOutlineSchema)
    chain = prompt | structured_llm
    return chain.invoke(
        {
            'source_material': source_material,
            'hint': hint or '(none)',
            'approx': approx,
        }
    )


def generate_preference_content(preferences: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """You are an expert content creator for a WhatsApp learning bot.
        Generate comprehensive, engaging educational content.

        Rules:
        - Structure 'topic_content' into 3-5 logical sections.
        - Use the delimiter [BITE_BREAK] between sections.
        - Use emojis, short paragraphs, and an engaging tone.""",
            ),
            ('human', 'User Preference: {preferences}'),
        ]
    )

    llm = _bedrock_llm()
    structured_llm = llm.with_structured_output(PreferencesSchema)
    chain = prompt | structured_llm
    return chain.invoke({'preferences': preferences})

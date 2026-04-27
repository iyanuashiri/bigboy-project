from typing import List

from pydantic import BaseModel, Field


class InstructionalBite(BaseModel):
    title: str = Field(
        max_length=120,
        description='Short label for the bite, e.g. "Definition", "Chemical equation", "Trade-offs".',
    )
    content: str = Field(
        description='Substantive bite: one to four short paragraphs the learner can retain; '
        'self-contained and grounded in the topic material (not a section heading alone).',
    )


class InstructionalBitesSchema(BaseModel):
    bites: List[InstructionalBite] = Field(
        description='Ordered smallest useful knowledge units for this topic.',
        min_length=1,
        max_length=18,
    )


class PlannedTopic(BaseModel):
    name: str = Field(max_length=200, description='Concise topic title')
    description: str = Field(
        description='One sentence describing what the learner masters in this topic.',
    )
    content: str = Field(
        description='Focused teaching material for this topic only: excerpts, tight paraphrase, '
        'or structured notes grounded in the source (enough detail for downstream bites and quizzes).',
    )


class CurriculumOutlineSchema(BaseModel):
    topics: List[PlannedTopic] = Field(
        min_length=2,
        max_length=14,
        description='Distinct, non-overlapping topics that cover the source in a sensible teaching order.',
    )


class PreferencesSchema(BaseModel):
    preferences: str = Field(description='User preferences for generating topic content')
    topic_content: str = Field(description='Generated topic content based on user preferences')
    topic_name: str = Field(description='Generated topic name based on user preferences')
    topic_description: str = Field(description='Generated topic description based on user preferences')
    subject_name: str = Field(description='Generated subject name based on user preferences')
    subject_description: str = Field(description='Generated subject description based on user preferences')

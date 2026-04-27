from pydantic import BaseModel, Field


class DocumentCategoryLabelSchema(BaseModel):
    name: str = Field(
        max_length=200,
        description='Short library title, 3–10 words, no trailing punctuation.',
    )
    description: str = Field(
        description='One or two sentences summarizing what these documents cover together.',
    )

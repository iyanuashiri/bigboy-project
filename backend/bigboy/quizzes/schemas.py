from typing import List, Dict

from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question")
    options: List[str] = Field(description="List of options")
    answer: str = Field(description="The correct answer in UPPERCASE")


class QuizSchema(BaseModel):
    quizzes: List[QuizQuestion]

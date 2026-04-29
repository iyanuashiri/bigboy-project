from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock

from config.bedrock_client import aws_boto_client_kwargs

from bigboy.quizzes.schemas import QuizSchema


def generate_quizzes(number_of_questions, number_of_options, text):
    prompt = ChatPromptTemplate.from_template(
        "Generate exactly {number_of_questions} multiple-choice questions from the text.\n"
        "Each question must have exactly {number_of_options} options as plain strings.\n"
        "For each question, set `answer` to match one of the options **verbatim** (same spelling and casing as that option).\n"
        "Only one option should match `answer`.\n\n"
        "Text:\n{text}"
    )

    llm = ChatBedrock(
        model_id=settings.BEDROCK_MODEL_ID,
        **aws_boto_client_kwargs(),
    )
    structured_llm = llm.with_structured_output(QuizSchema)
    chain = prompt | structured_llm
    response = chain.invoke({
        "number_of_questions": number_of_questions,
        "number_of_options": number_of_options,
        "text": text
    })
    
    return response
    
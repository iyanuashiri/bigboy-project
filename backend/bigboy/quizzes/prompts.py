from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
from decouple import config

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
        model_id="global.amazon.nova-2-lite-v1:0",
        region_name="us-east-2",
        aws_access_key_id=config("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"),
    )
    structured_llm = llm.with_structured_output(QuizSchema)
    chain = prompt | structured_llm
    response = chain.invoke({
        "number_of_questions": number_of_questions,
        "number_of_options": number_of_options,
        "text": text
    })
    
    return response


# a = generate_quizzes(5, 4, "The capital of France is Paris. The capital of Germany is Berlin. The capital of Italy is Rome.")

# print(a)


# print("Iyanuoluwa Ajao, Iyanuoluwa Ajao")
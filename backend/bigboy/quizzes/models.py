from django.db import models

from bigboy.subjects.models import Subject, Topic
from bigboy.quizzes.prompts import generate_quizzes
from bigboy.accounts.models import Account

# Create your models here.


class QuizManager(models.Manager):
    def get_questions_by_subject(self, subject_id):
        """Fetches all quizzes related to a specific subject."""
        quiz = self.filter(subject_id=subject_id)[0] if self.filter(subject_id=subject_id).exists() else None
        if not quiz:
            return None
        questions = quiz.get_questions()
        return questions
        

class Quiz(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='subject_quizzes')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic_quizzes')
    number_of_questions = models.IntegerField()
    number_of_options = models.IntegerField(default=4)

    class Meta:
        verbose_name = 'quiz'
        verbose_name_plural = 'quizzes' 

    objects = QuizManager()    

    def __str__(self):
        return self.topic.name

    def generate_questions(self):
        response = generate_quizzes(
            self.number_of_questions,
            self.number_of_options,
            self.topic.content,
        )
        items = getattr(response, 'quizzes', None) or []
        created = 0
        max_q = max(0, int(self.number_of_questions))
        max_o = max(2, min(8, int(self.number_of_options)))

        for q_data in items[:max_q]:
            if isinstance(q_data, dict):
                q_text = str(q_data.get('question', '')).strip()
                options = list(q_data.get('options') or [])
                answer = str(q_data.get('answer', '')).strip()
            else:
                q_text = str(getattr(q_data, 'question', '') or '').strip()
                options = list(getattr(q_data, 'options', None) or [])
                answer = str(getattr(q_data, 'answer', '') or '').strip()

            if not q_text or not options:
                continue

            question_obj = Question.objects.create(quiz=self, question=q_text)
            answer_norm = answer.casefold()
            for raw in options[:max_o]:
                opt_text = str(raw or '').strip()
                if not opt_text:
                    continue
                stored = opt_text[:100]
                is_correct = bool(answer_norm) and opt_text.casefold() == answer_norm
                Option.objects.create(
                    question=question_obj,
                    option=stored,
                    is_correct=is_correct,
                    explanation='',
                    reason='',
                )
            created += 1

        return created
    
    def get_questions(self):
        """Fetches all questions related to this quiz and their options."""
        list_of_dictionaries = []

        questions = self.quiz_questions.all()
        for question in questions:
            options = question.question_options.all()
            question_dict = {
                "question": question.question,
                "question_id": question.id,
                "options": [{"option": option.option, "is_correct": option.is_correct, "option_id": option.id} for option in options]
            }
            list_of_dictionaries.append(question_dict)
        return list_of_dictionaries    



class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_questions')
    question = models.TextField()

    class Meta:
        verbose_name = 'question'
        verbose_name_plural = 'questions' 

    def __str__(self):
        return self.question    


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_options')
    option = models.CharField(max_length=100)
    is_correct = models.BooleanField(default=False)
    explanation = models.CharField(max_length=1000, default="")
    reason = models.CharField(max_length=1000, default="")

    class Meta:
        verbose_name = 'option'
        verbose_name_plural = 'options' 

    def __str__(self):
        return self.option    


class Answer(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_answers')
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='option_answers')
    
    class Meta:
        verbose_name = 'answer'
        verbose_name_plural = 'answers' 

    def __str__(self):
        return f"{self.account} answered {self.question}"
    
    def is_correct(self):
        return self.selected_option.is_correct

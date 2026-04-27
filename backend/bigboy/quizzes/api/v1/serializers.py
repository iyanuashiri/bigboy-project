import random

from rest_framework import serializers

from bigboy.quizzes.models import Answer, Quiz, Question, Option
from bigboy.subjects.api.v1.serializers import SubjectSerializer, TopicSerializer
from bigboy.subjects.models import Enrollment, Subject, Topic


class QuizSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())
    
    class Meta:
        model = Quiz
        fields = ('id', 'subject', 'topic', 'number_of_questions', 'number_of_options')

    def validate(self, attrs):
        request = self.context.get('request')
        if self.instance:
            subject = attrs.get('subject', self.instance.subject)
            topic = attrs.get('topic', self.instance.topic)
        else:
            subject = attrs.get('subject')
            topic = attrs.get('topic')
        if subject is not None and topic is not None and topic.subject_id != subject.id:
            raise serializers.ValidationError('Topic does not belong to this subject.')
        if request and getattr(request, 'user', None) and request.user.is_authenticated and subject is not None:
            if not Enrollment.objects.filter(account=request.user, subject=subject).exists():
                raise serializers.ValidationError('You must be enrolled in this subject to create a quiz.')
        return attrs

    def create(self, validated_data):
        quiz = Quiz.objects.create(**validated_data)
        quiz.generate_questions()
        return quiz


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'question', 'option', 'is_correct', 'explanation', 'reason')


class QuestionSerializer(serializers.ModelSerializer):
    question_options = OptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'quiz', 'question', 'question_options')


class QuizReadSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    quiz_questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'subject', 'topic', 'number_of_questions', 'number_of_options', 'quiz_questions')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for q in data.get('quiz_questions') or []:
            opts = q.get('question_options')
            if opts and len(opts) > 1:
                random.shuffle(opts)
        return data


class QuizAnswerSubmitSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_option = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all())

    def validate(self, attrs):
        question = attrs['question']
        option = attrs['selected_option']
        if option.question_id != question.id:
            raise serializers.ValidationError({'selected_option': 'Option does not belong to this question.'})
        user = self.context['request'].user
        quiz = question.quiz
        if not Enrollment.objects.filter(account=user, subject=quiz.subject).exists():
            raise serializers.ValidationError('You are not enrolled in this quiz\'s subject.')
        if Answer.objects.filter(account=user, question=question).exists():
            raise serializers.ValidationError({'question': 'This question has already been answered.'})
        return attrs

from rest_framework import serializers

from bigboy.subjects.models import Subject, Topic, Bite, Enrollment


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'description')


class TopicBitesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bite
        fields = ('id', 'name', 'bite', 'is_locked')


class BiteUpdateSerializer(serializers.ModelSerializer):
    topic = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Bite
        fields = ('id', 'topic', 'name', 'bite', 'is_locked')
        read_only_fields = ('id', 'topic')


class SubjectTopicsSerializer(serializers.ModelSerializer):
    topic_bites = TopicBitesSerializer(many=True, read_only=True)
    bite_count = serializers.SerializerMethodField()
    quiz_id = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'description',
            'content',
            'topic_bites',
            'bite_count',
            'quiz_id',
        )

    def get_bite_count(self, obj):
        return len(obj.topic_bites.all())

    def get_quiz_id(self, obj):
        q = obj.topic_quizzes.order_by('id').first()
        return q.id if q else None


class SubjectReadSerializer(serializers.ModelSerializer):
    subject_topics = SubjectTopicsSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subject
        fields = ('id', 'name', 'description', 'subject_topics')


class SubjectCatalogSerializer(serializers.ModelSerializer):
    """Browse subjects before enrollment (no nested topic content)."""

    class Meta:
        model = Subject
        fields = ('id', 'name', 'description')


class TopicSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())

    class Meta:
        model = Topic
        fields = ('id', 'subject', 'name', 'description', 'content')    

    def create(self, validated_data):
        topic = Topic.objects.create(**validated_data)
        topic.generate_bites()
        return topic


class TopicReadSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer()
    topic_bites = TopicBitesSerializer(many=True, read_only=True)
    
    class Meta:
        model = Topic
        fields = ('id', 'subject', 'name', 'description', 'content', 'topic_bites')


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ('id', 'subject', 'date_enrolled')
        read_only_fields = ('id', 'date_enrolled')

    def validate_subject(self, subject):
        user = self.context['request'].user
        if Enrollment.objects.filter(account=user, subject=subject).exists():
            raise serializers.ValidationError('Already enrolled in this subject.')
        return subject


class EnrollmentReadSerializer(serializers.ModelSerializer):
    subject = SubjectCatalogSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'subject', 'date_enrolled')
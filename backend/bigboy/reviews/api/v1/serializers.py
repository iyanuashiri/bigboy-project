from rest_framework import serializers

from bigboy.reviews.models import BiteReviewState, SubjectWeeklyGoal


class ReviewDueSerializer(serializers.ModelSerializer):
    subject_id = serializers.IntegerField(source='bite.topic.subject_id', read_only=True)
    subject_name = serializers.CharField(source='bite.topic.subject.name', read_only=True)
    topic_id = serializers.IntegerField(source='bite.topic_id', read_only=True)
    topic_name = serializers.CharField(source='bite.topic.name', read_only=True)
    bite_name = serializers.CharField(source='bite.name', read_only=True)
    bite_body = serializers.CharField(source='bite.bite', read_only=True)
    is_locked = serializers.BooleanField(source='bite.is_locked', read_only=True)

    class Meta:
        model = BiteReviewState
        fields = (
            'id',
            'bite',
            'subject_id',
            'subject_name',
            'topic_id',
            'topic_name',
            'bite_name',
            'bite_body',
            'is_locked',
            'interval_days',
            'repetitions',
            'next_review_at',
            'last_grade',
        )
        read_only_fields = fields


class ReviewGradeSerializer(serializers.Serializer):
    grade = serializers.ChoiceField(choices=BiteReviewState.Grade.choices)


class SubjectWeeklyGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectWeeklyGoal
        fields = ('id', 'subject', 'weekly_bite_target', 'active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_subject(self, subject):
        user = self.context['request'].user
        if not subject.subject_enrollments.filter(account=user).exists():
            raise serializers.ValidationError('You must be enrolled in this subject.')
        return subject

    def validate(self, attrs):
        user = self.context['request'].user
        subject = attrs.get('subject') or (self.instance.subject if self.instance else None)
        if subject and self.instance is None:
            if SubjectWeeklyGoal.objects.filter(account=user, subject=subject).exists():
                raise serializers.ValidationError(
                    {'subject': 'A goal already exists for this subject; update it instead.'},
                )
        return attrs


class SubjectWeeklyGoalReadSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    completed_this_week = serializers.SerializerMethodField()

    class Meta:
        model = SubjectWeeklyGoal
        fields = (
            'id',
            'subject',
            'subject_name',
            'weekly_bite_target',
            'active',
            'completed_this_week',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'subject',
            'subject_name',
            'weekly_bite_target',
            'active',
            'completed_this_week',
            'created_at',
            'updated_at',
        )

    def get_completed_this_week(self, obj):
        from bigboy.reviews.services.goals import bites_completed_this_week

        return bites_completed_this_week(
            account=self.context['request'].user,
            subject_id=obj.subject_id,
        )

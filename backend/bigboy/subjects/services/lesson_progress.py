from __future__ import annotations

from django.db import transaction

from bigboy.accounts.models import Point
from bigboy.reviews.services.review_hooks import schedule_initial_review_after_bite_learned
from bigboy.subjects.api.v1.scoping import is_enrolled
from bigboy.subjects.models import Bite, Checkpoint, Enrollment, Milestone, Subject, Topic


def _ordered_bites_for_subject(subject: Subject):
    for topic in subject.subject_topics.order_by('id'):
        for bite in topic.topic_bites.order_by('id'):
            yield topic, bite


def bite_has_completed_checkpoint(account, bite_id: int) -> bool:
    return Checkpoint.objects.filter(
        account=account,
        bite_id=bite_id,
        status=Checkpoint.Status.COMPLETED,
    ).exists()


def first_incomplete_bite_id(account, subject: Subject) -> int | None:
    for _topic, bite in _ordered_bites_for_subject(subject):
        if not bite_has_completed_checkpoint(account, bite.id):
            return bite.id
    return None


def build_subject_progress(account, subject: Subject) -> dict:
    topics_out = []
    for topic in subject.subject_topics.order_by('id'):
        milestone_done = Milestone.objects.filter(account=account, topic=topic).exists()
        bites_out = []
        for bite in topic.topic_bites.order_by('id'):
            bites_out.append({
                'id': bite.id,
                'name': bite.name,
                'completed': bite_has_completed_checkpoint(account, bite.id),
            })
        topics_out.append({
            'id': topic.id,
            'name': topic.name,
            'milestone_completed': milestone_done,
            'bites': bites_out,
        })
    return {
        'subject_id': subject.id,
        'topics': topics_out,
        'first_incomplete_bite_id': first_incomplete_bite_id(account, subject),
    }


def complete_bite_for_user(account, bite_id: int) -> dict:
    bite = Bite.objects.select_related('topic__subject').get(pk=bite_id)
    subject = bite.topic.subject
    if not is_enrolled(account, subject.id):
        raise PermissionError('Not enrolled in this subject.')

    expected = first_incomplete_bite_id(account, subject)
    if expected is None:
        raise ValueError('All bites in this subject are already completed.')
    if bite_id != expected:
        raise ValueError('Complete bites in order; a prior bite is still incomplete.')

    if bite_has_completed_checkpoint(account, bite_id):
        raise ValueError('This bite is already marked complete.')

    topic = bite.topic
    bite_ids = list(topic.topic_bites.order_by('id').values_list('id', flat=True))
    is_last_bite_in_topic = bite_ids and bite_id == bite_ids[-1]

    with transaction.atomic():
        Checkpoint.objects.create(
            bite=bite,
            account=account,
            status=Checkpoint.Status.COMPLETED,
        )
        Point.objects.award_bite_completed(account=account)
        milestone_created = False
        if is_last_bite_in_topic:
            _, created = Milestone.objects.get_or_create(
                topic=topic,
                account=account,
                defaults={'completed': True},
            )
            milestone_created = created
            if milestone_created:
                Point.objects.award_milestone_achieved(account=account)

    schedule_initial_review_after_bite_learned(account=account, bite_id=bite_id)

    return {
        'bite_id': bite_id,
        'topic_id': topic.id,
        'subject_id': subject.id,
        'milestone_created': milestone_created,
        'next_incomplete_bite_id': first_incomplete_bite_id(account, subject),
    }

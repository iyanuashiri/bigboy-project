from django.db.models import QuerySet

from bigboy.subjects.models import Enrollment, Subject


def enrolled_subject_ids_for(account) -> QuerySet:
    return Enrollment.objects.filter(account=account).values_list('subject_id', flat=True)


def is_enrolled(account, subject_id: int) -> bool:
    return Enrollment.objects.filter(account=account, subject_id=subject_id).exists()


def subjects_queryset_for_user(account, scope: str) -> QuerySet:
    qs = Subject.objects.all().order_by('id')
    if scope == 'catalog':
        return qs
    return qs.filter(subject_enrollments__account=account).distinct()

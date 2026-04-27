from django.contrib import admin

from bigboy.reviews.models import BiteReviewState, SubjectWeeklyGoal


@admin.register(BiteReviewState)
class BiteReviewStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'bite', 'next_review_at', 'interval_days', 'last_grade')
    list_filter = ('last_grade',)
    raw_id_fields = ('account', 'bite')


@admin.register(SubjectWeeklyGoal)
class SubjectWeeklyGoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'subject', 'weekly_bite_target', 'active')
    list_filter = ('active',)
    raw_id_fields = ('account', 'subject')

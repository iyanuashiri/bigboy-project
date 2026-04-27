import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subjects', '0002_bite_is_locked'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubjectWeeklyGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekly_bite_target', models.PositiveSmallIntegerField(default=5)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'account',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='subject_weekly_goals',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'subject',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='weekly_goals',
                        to='subjects.subject',
                    ),
                ),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(
                        fields=('account', 'subject'),
                        name='reviews_subjectweeklygoal_account_subject_uniq',
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name='BiteReviewState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interval_days', models.PositiveSmallIntegerField(default=1)),
                ('repetitions', models.PositiveIntegerField(default=0)),
                ('next_review_at', models.DateTimeField(db_index=True)),
                ('last_reviewed_at', models.DateTimeField(blank=True, null=True)),
                (
                    'last_grade',
                    models.CharField(
                        blank=True,
                        choices=[
                            ('again', 'Again'),
                            ('hard', 'Hard'),
                            ('good', 'Good'),
                            ('easy', 'Easy'),
                        ],
                        max_length=8,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'account',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bite_review_states',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'bite',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='review_states',
                        to='subjects.bite',
                    ),
                ),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(
                        fields=('account', 'bite'),
                        name='reviews_bitereviewstate_account_bite_uniq',
                    )
                ],
                'indexes': [models.Index(fields=['account', 'next_review_at'], name='reviews_bit_acc_next_idx')],
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bite',
            name='is_locked',
            field=models.BooleanField(
                default=False,
                help_text='When true, this bite is preserved during topic bite regeneration.',
            ),
        ),
    ]

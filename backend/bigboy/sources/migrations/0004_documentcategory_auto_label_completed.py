from django.db import migrations, models


def mark_existing_categories_labeled(apps, schema_editor):
    DocumentCategory = apps.get_model('sources', 'DocumentCategory')
    DocumentCategory.objects.update(auto_label_completed=True)


class Migration(migrations.Migration):

    dependencies = [
        ('sources', '0003_documentchunk_rag'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentcategory',
            name='auto_label_completed',
            field=models.BooleanField(
                default=False,
                help_text='When true, name/description were finalized (or user had a pre-migration category).',
            ),
        ),
        migrations.RunPython(mark_existing_categories_labeled, migrations.RunPython.noop),
    ]

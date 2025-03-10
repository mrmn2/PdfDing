from django.db import migrations, models
from pdf.service import PdfProcessingServices


def adjust_thumbnails(apps, schema_editor):
    """Regenerate thumbnail images after changing thumbnail dimensions"""

    pdf_model = apps.get_model("pdf", "Pdf")

    for pdf_object in pdf_model.objects.all():
        PdfProcessingServices.process_with_pypdfium(pdf_object, delete_existing_thumbnail_and_preview=True)


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_activiate_nested_tags_overview'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='pdfs_per_page',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='show_progress_bars',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='show_thumbnails',
        ),
        migrations.AddField(
            model_name='profile',
            name='layout',
            field=models.CharField(
                choices=[('Compact', 'Compact'), ('List', 'List'), ('Grid', 'Grid')], default='Compact', max_length=7
            ),
        ),
        migrations.RunPython(adjust_thumbnails, reverse_func),
    ]

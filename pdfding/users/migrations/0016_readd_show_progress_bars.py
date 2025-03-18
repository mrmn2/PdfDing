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
        ('users', '0015_add_pdf_overview_layouts'),
        ('pdf', '0014_add_pdf_revision'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='show_progress_bars',
            field=models.CharField(
                choices=[('Enabled', 'Enabled'), ('Disabled', 'Disabled')], default='Enabled', max_length=8
            ),
        ),
        migrations.RunPython(adjust_thumbnails, reverse_func),
    ]

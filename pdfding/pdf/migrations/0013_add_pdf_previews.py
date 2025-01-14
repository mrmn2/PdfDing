import pdf.models
from django.db import migrations, models
from pdf.service import process_with_pypdfium


def fill_thumbnails_and_previews(apps, schema_editor):
    """Fill the thumbnails and previews for all pdfs."""

    pdf_model = apps.get_model("pdf", "Pdf")

    for pdf_object in pdf_model.objects.all():
        process_with_pypdfium(pdf_object)


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0012_add_pdf_thumbnails'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdf',
            name='preview',
            field=models.FileField(null=True, upload_to=pdf.models.get_preview_path),
        ),
        migrations.RunPython(fill_thumbnails_and_previews, reverse_func),
    ]

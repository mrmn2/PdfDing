from django.db import migrations
from pdf.service import rename_pdf


def update_pdf_file_names(apps, schema_editor):
    """Rename pdfs, so that the file name is not a random ID but the pdf name."""

    pdf_model = apps.get_model("pdf", "Pdf")

    for pdf in pdf_model.objects.all():
        rename_pdf(pdf, pdf.name)


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):

    dependencies = [('pdf', '0015_add_comments_highlights')]

    operations = [
        migrations.RunPython(update_pdf_file_names, reverse_func),
    ]

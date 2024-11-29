from django.db import migrations, models
from pypdf import PdfReader


def fill_number_of_pages(apps, schema_editor):
    """Fill the number of pages for all pdfs."""

    pdf_model = apps.get_model("pdf", "Pdf")

    for pdf in pdf_model.objects.all():
        # try to set the page numbers
        try:
            reader = PdfReader(pdf.file.path)
            pdf.number_of_pages = len(reader.pages)
            pdf.save()
        except:  # noqa
            print(f'Could not get number of pages from PDF "{pdf.name}" of user "{pdf.owner.user.email}".')


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('pdf', '0006_increase_pdf_model_name_lenghts_to_150'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdf',
            name='number_of_pages',
            field=models.IntegerField(default=1),
        ),
        migrations.RunPython(fill_number_of_pages, reverse_func),
    ]

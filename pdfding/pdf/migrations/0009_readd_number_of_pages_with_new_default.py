# Readd the number_of_pages migration in order to not display a progress bar if the number of
# pages could not be extracted via pypdf. Some user have already migrated to the previous migration.
# Therefore, we delete the migration, so these users get the same behaviour.

from django.db import migrations, models
from pdf.service import set_number_of_pages


def fill_number_of_pages(apps, schema_editor):
    """Fill the number of pages for all pdfs."""

    pdf_model = apps.get_model("pdf", "Pdf")

    for pdf in pdf_model.objects.all():
        set_number_of_pages(pdf)


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0008_tmp_remove_number_of_pages'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdf',
            name='number_of_pages',
            field=models.IntegerField(default=-1),
        ),
        migrations.RunPython(fill_number_of_pages, reverse_func),
    ]

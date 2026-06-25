import django.db.models.deletion
from django.db import migrations, models


def set_metadata_title(apps, schema_editor):
    """Set the metadata title to the current PDF name."""

    pdf_model = apps.get_model("pdf", "Pdf")
    pdf_metadata_model = apps.get_model("pdf", "Metadata")
    db_alias = schema_editor.connection.alias

    for pdf_object in pdf_model.objects.all():
        pdf_metadata_model.objects.using(db_alias).create(title=pdf_object.name, pdf_id=pdf_object.id)


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0028_remove_unneeded_fields_from_shared_collection'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authors', models.CharField(blank=True, max_length=256)),
                ('abstract', models.TextField(blank=True, default='', help_text='Optional')),
                ('doi', models.CharField(blank=True, max_length=128)),
                ('issue', models.CharField(blank=True, max_length=64)),
                ('journal', models.CharField(blank=True, max_length=128)),
                ('keywords', models.TextField(blank=True, help_text='Optional')),
                ('pages', models.CharField(blank=True, max_length=32)),
                ('publisher', models.CharField(blank=True, max_length=64)),
                (
                    'reference_type',
                    models.CharField(
                        blank=True,
                        choices=[
                            ('Article', 'Article'),
                            ('Book', 'Book'),
                            ('Booklet', 'Booklet'),
                            ('Conference', 'Conference'),
                            ('Inbook', 'Inbook'),
                            ('Incollection', 'Incollection'),
                            ('Inproceedings', 'Inproceedings'),
                            ('Manual', 'Manual'),
                            ('Masterthesis', 'Masterthesis'),
                            ('Misc', 'Misc'),
                            ('Phdthesis', 'Phdthesis'),
                            ('Proceedings', 'Proceedings'),
                            ('Techreport', 'Techreport'),
                            ('Unpublished', 'Unpublished'),
                        ],
                        max_length=32,
                    ),
                ),
                ('title', models.CharField(max_length=512)),
                ('url', models.CharField(blank=True, max_length=128)),
                ('volume', models.CharField(max_length=16)),
                ('pdf', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='pdf.pdf')),
            ],
        ),
        migrations.RunPython(set_metadata_title, reverse_func),
    ]

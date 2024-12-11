from django.db import migrations, models


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
    ]

# Generated by Django 5.0.6 on 2024-06-23 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0002_change_pdf_and_tag_model_id_to_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdf',
            name='current_page',
            field=models.IntegerField(default=1),
        ),
    ]

# Generated by Django 5.0.7 on 2024-07-16 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0001_add_pdf_and_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdf',
            name='views',
            field=models.IntegerField(default=0),
        ),
    ]
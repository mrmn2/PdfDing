# Generated by Django 5.1.1 on 2024-11-12 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0005_add_last_viewed_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pdf',
            name='name',
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='sharedpdf',
            name='name',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
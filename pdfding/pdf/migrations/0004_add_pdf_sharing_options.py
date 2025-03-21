# Generated by Django 5.1.1 on 2024-10-22 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0003_add_pdf_sharing'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharedpdf',
            name='deletion_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sharedpdf',
            name='expiration_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sharedpdf',
            name='max_views',
            field=models.IntegerField(blank=True, help_text='Optional', null=True),
        ),
        migrations.AddField(
            model_name='sharedpdf',
            name='password',
            field=models.CharField(blank=True, help_text='Optional', max_length=128, null=True),
        ),
    ]

# Generated by Django 5.1.5 on 2025-03-13 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_readd_show_progress_bars'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='annotation_sorting',
            field=models.CharField(
                choices=[('Newest', 'Newest'), ('Oldest', 'Oldest')], default='Newest', max_length=15
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_activiate_nested_tags_overview'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='pdfs_per_page',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='show_progress_bars',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='show_thumbnails',
        ),
        migrations.AddField(
            model_name='profile',
            name='layout',
            field=models.CharField(
                choices=[('Compact', 'Compact'), ('List', 'List'), ('Grid', 'Grid')], default='Compact', max_length=7
            ),
        ),
    ]

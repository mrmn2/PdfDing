from django.db import migrations, models
from users.models import Profile


def set_pdf_stats(profile: Profile) -> None:  # pragma: no cover
    """Set PDF stats of a profile"""

    pass


def add_pdf_stats(apps, schema_editor):  # pragma: no cover
    """Add PDF stats to all profiles."""

    profile_model = apps.get_model("users", "Profile")

    for profile_object in profile_model.objects.all():
        set_pdf_stats(profile_object)


def reverse_func(apps, schema_editor):  # pragma: no cover
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_add_signatures'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='number_of_pdfs',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='pdfs_total_size',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(add_pdf_stats, reverse_func),
    ]

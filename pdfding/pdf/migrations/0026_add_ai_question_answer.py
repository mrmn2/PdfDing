# Generated manually on 2026-01-03 to add PdfAIQuestionAnswer model

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0025_add_creation_date_to_ws_collections'),
    ]

    operations = [
        migrations.CreateModel(
            name='PdfAIQuestionAnswer',
            fields=[
                ('creation_date', models.DateTimeField(editable=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('page', models.IntegerField()),
                ('text', models.TextField()),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('pdf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pdf.pdf')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]


# Generated by Django 3.0.2 on 2020-02-04 20:28

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('hazard_feed', '0005_auto_20200204_2313'),
    ]

    operations = [
        migrations.AddField(
            model_name='weatherrecipients',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]

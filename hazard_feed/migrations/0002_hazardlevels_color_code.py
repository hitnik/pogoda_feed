# Generated by Django 3.0.2 on 2020-01-26 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hazard_feed', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hazardlevels',
            name='color_code',
            field=models.CharField(max_length=6, null=True),
        ),
    ]

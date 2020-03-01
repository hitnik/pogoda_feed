# Generated by Django 3.0.2 on 2020-02-28 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hazard_feed', '0011_rss_feed_url_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='weatherrecipients',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='weatherrecipients',
            name='date_modified',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]

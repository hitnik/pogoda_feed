from django.apps import AppConfig
from django.db.models.signals import post_save
import os
import django_rq
import datetime
from redis.exceptions import ConnectionError



class HazardFeedConfig(AppConfig):
    """
     app settings. You must specify settings in your environment
    """
    name = 'hazard_feed'
    WEATHER_EMAIL_SMTP_HOST = os.getenv('EMAIL_WEATHER_SMTP_HOST')
    WEATHER_USE_TSL = int(os.getenv('WEATHER_USE_TSL', 0))
    WEATHER_EMAIL_SMTP_PORT = os.getenv('WEATHER_EMAIL_SMTP_PORT')
    WEATHER_EMAIL_HOST_USER = os.getenv('WEATHER_EMAIL_HOST_USER')
    WEATHER_EMAIL_HOST_PASSWORD = os.getenv('WEATHER_EMAIL_HOST_PASSWORD')

    def ready(self):
        from .models import HazardFeeds
        from .signals import send_hazard_feed_notification
        post_save.connect(send_hazard_feed_notification, sender=HazardFeeds)
        from . import jobs

        try:
            scheduler = django_rq.get_scheduler('default')
            scheduler.schedule(scheduled_time=datetime.datetime.utcnow() + datetime.timedelta(seconds=5),
                               func=jobs.parse_feeds,
                               interval=60*10
                               )
        except ConnectionError:
            pass
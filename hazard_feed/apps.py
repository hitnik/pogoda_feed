from django.apps import AppConfig
import os
import django_rq
import datetime
from rq_scheduler import Scheduler
from .jobs import parse_feeds

class HazardFeedConfig(AppConfig):
    """
     app settings. You must specify settings in your environment or create file env.py in your project root
    """
    name = 'hazard_feed'
    WEATHER_EMAIL_FROM = 'Телекс ОДО <telex@mck.beltelecom.by>'
    WEATHER_EMAIL_SMTP_HOST = os.getenv('EMAIL_WEATHER_SMTP_HOST')
    WEATHER_USE_TSL = os.getenv('USE_TSL')
    WEATHER_EMAIL_SMTP_PORT = os.getenv('WEATHER_EMAIL_SMTP_PORT')
    WEATHER_EMAIL_HOST_USER = os.getenv('WEATHER_EMAIL_HOST_USER')
    WEATHER_EMAIL_HOST_PASSWORD = os.getenv('WEATHER_EMAIL_HOST_PASSWORD')

    def ready(self):
        queue = django_rq.get_queue('default')
        scheduler = Scheduler(queue=queue)
        scheduler.schedule(scheduled_time=datetime.datetime.utcnow()+datetime.timedelta(minutes=2),
                           func=parse_feeds,
                           interval=60*20
                           )
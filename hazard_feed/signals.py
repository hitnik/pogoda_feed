from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HazardFeeds
import datetime
import django_rq
from .jobs import send_weather_mail

def send_hazard_feed_notification(sender, instance, created, **kwargs):
    if created \
            and not instance.is_sent:
            # and (
            #     instance.date.date() == instance.date_modified.date()
            #     or instance.is_newer_that(datetime.timedelta(hours=1))
            # )
            # :
        queue = django_rq.get_queue()
        queue.enqueue(send_weather_mail, instance)
        instance.is_sent = True
        instance.save()

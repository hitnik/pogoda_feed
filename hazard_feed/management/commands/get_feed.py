from django.core.management.base import BaseCommand, CommandError
from hazard_feed.config import WEATHER_FEED_URL
from hazard_feed.utils import (
    parse_weather_feeds, put_feed_to_db,
    make_weather_hazard_message, send_weather_mail
    )
import datetime

class Command(BaseCommand):

    def handle(self, *args, **options):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        for feed in feeds:
            put_result = put_feed_to_db(feed)
            if put_result and \
                    (
                        feed.date.date() == feed.date_modified.date() or
                        feed.is_newer_that(datetime.timedelta(hours=1))
                    ):
                msg = make_weather_hazard_message(feed)
                send_weather_mail(msg)
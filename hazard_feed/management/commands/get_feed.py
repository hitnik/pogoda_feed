from django.core.management.base import BaseCommand, CommandError
import feedparser
import time
import pytz
import datetime
from weather_danger_feed.config import WEATHER_FEED_URL

class Command(BaseCommand):

    def handle(self, *args, **options):
        feeds = feedparser.parse(WEATHER_FEED_URL)
        for feed in feeds.entries:
            ms = int(time.mktime(feed.updated_parsed))
            date = datetime.datetime.fromtimestamp(ms).replace(tzinfo=pytz.utc)

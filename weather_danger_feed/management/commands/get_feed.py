from django.core.management.base import BaseCommand, CommandError
import feedparser
from weather_danger_feed.config import WEATHER_FEED_URL

class Command(BaseCommand):

    def handle(self, *args, **options):
        feed = feedparser.parse(WEATHER_FEED_URL)
        date = feed.entries[0].updated_parsed
        print(date)
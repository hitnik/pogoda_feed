import feedparser
from workers import task
from .config import WEATHER_FEED_URL

@task()
def get_danger_feed():
    feed = feedparser.parse(WEATHER_FEED_URL)
    print(feed.entries)


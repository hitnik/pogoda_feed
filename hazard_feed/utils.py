import re
import feedparser
import time
import datetime
import pytz
from .models import HazardLevels, HazardFeeds

def hazard_level_in_text_find(text):
    """
    chek if hazard level in text
    :param text:
    :return:
    """
    for hazard in HazardLevels.objects.all():
        if re.search(hazard.title, text):
            return hazard
    return None

def parse_weather_feeds(url):
    """
    parse weather hazard rss to django model
    :param url:url of weather page
    :return:
    """
    feeds = feedparser.parse(url)
    feeds_out = []
    for feed in feeds.entries:
        ms = int(time.mktime(feed.published_parsed))
        date = datetime.datetime.fromtimestamp(ms).replace(tzinfo=pytz.utc)
        date_parsed = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        hazard_level = hazard_level_in_text_find(feed.summary)
        if hazard_level:
            hazard_feed = HazardFeeds(
                id=feed.id, date=date, title=feed.title,
                link=feed.link, summary=feed.summary,
                date_modified=date_parsed, hazard_level=hazard_level
            )
            feeds_out.append(hazard_feed)
    return feeds_out

def put_feed_to_db(feed):
    if not HazardFeeds.objects.filter(id=feed.id).exists():
        feed.save()
        return True
    return False


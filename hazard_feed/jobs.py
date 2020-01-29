from django_rq import job
from .config import WEATHER_FEED_URL
import asyncio
import datetime
from hazard_feed.utils import (
    parse_weather_feeds, put_feed_to_db,
    make_weather_hazard_message, send_weather_mail,
    get_weather_recipients
    )

@job()
def parse_and_send_feed():
    feeds = parse_weather_feeds(WEATHER_FEED_URL)
    recipients = get_weather_recipients()
    msg = make_weather_hazard_message(feeds[0])
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(send_weather_mail(msg, recipients))
    # for feed in feeds:
    #     put_result = put_feed_to_db(feed)
    #     if put_result and \
    #             (
    #                     feed.date.date() == feed.date_modified.date() or
    #                     feed.is_newer_that(datetime.timedelta(hours=1))
    #             ):
from django_rq import job
import asyncio
from .utils import (
    parse_weather_feeds, put_feed_to_db,
    make_weather_hazard_message, send_mail,
    get_weather_recipients, create_rss_urls_list,
    make_activation_code_message
    )

@job
def parse_feeds():
    urls_list = create_rss_urls_list()
    feeds = parse_weather_feeds(*urls_list)
    for feed in feeds:
        put_feed_to_db(feed)

@job
def send_weather_notification(feed):
    recipients = get_weather_recipients()
    msg = make_weather_hazard_message(feed)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_mail(msg, recipients))

@job
def send_activation_notification(code, recipients):
    msg = make_activation_code_message(code)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_mail(msg, recipients))



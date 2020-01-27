import re
import feedparser
import time
import datetime
import pytz
from .models import HazardLevels, HazardFeeds, WeatherRecipients
from django.conf import settings
import smtplib
import aiosmtplib
from django.template import loader
from asgiref.sync import sync_to_async
from email.message import EmailMessage
from bs4 import BeautifulSoup


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

def make_weather_hazard_message(feed):
    date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    local_tz = pytz.timezone(settings.TIME_ZONE)
    date = date.astimezone(local_tz)
    template = loader.get_template('hazard_feed/weather_mail.html')
    context = {'date': date, 'feed': feed}
    html = template.render(context)
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    msg = EmailMessage()
    msg['From'] = settings.WEATHER_EMAIL_FROM
    msg['Subject'] = feed.title
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')
    return msg

def get_weather_recipients():
    return list(WeatherRecipients.objects.filter(is_active=True).values_list('email', flat=True))

async def send_weather_mail(msg, recipients):

    """
    try to get queryset with async
    :param msg:
    :param recipients:
    :return:
    """
    recipients = await get_weather_recipients()

    await aiosmtplib.send(
        msg,
        hostname=settings.WEATHER_EMAIL_SMTP_HOST,
        port=settings.WEATHER_EMAIL_IMAP_PORT,
        use_tls=settings.WEATHER_USE_TSL,
        username=settings.WEATHER_EMAIL_HOST_USER,
        password=settings.WEATHER_EMAIL_HOST_PASSWORD,
        sender=settings.WEATHER_EMAIL_FROM,
        recipients=recipients
    )

# def get_weather_mail():

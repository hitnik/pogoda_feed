import re
import feedparser
import time
import datetime
import pytz
from .models import HazardLevels, HazardFeeds, WeatherRecipients
from django.conf import settings
import smtplib
from django.template import loader
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



def send_weather_mail(msg):

    recipients = list(WeatherRecipients.objects.filter(is_active=True).values_list('email', flat=True))
    smtp_server = smtplib.SMTP(host=settings.WEATHER_EMAIL_SMTP_HOST, port=settings.WEATHER_EMAIL_SMTP_PORT)
    if settings.WEATHER_USE_TSL:
        smtp_server.starttls()
    smtp_server.login(user=settings.WEATHER_EMAIL_SMTP_HOST_USER,
                        password=settings.WEATHER_EMAIL_SMTP_HOST_PASSWORD)
    smtp_server.ehlo()
    smtp_server.send_message(msg, to_addrs=recipients)
    smtp_server.quit()
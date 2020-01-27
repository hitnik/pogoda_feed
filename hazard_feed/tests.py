from django.test import TestCase, override_settings
from .utils import *
from .config import WEATHER_FEED_URL
from .models import WeatherRecipients
import asyncio
import os
import env
from django.conf import settings


class TestUtils(TestCase):
    fixtures = ['hazard_feed/fixtures/hazard_levels.json']

    def setUp(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        feeds[0].save()
        WeatherRecipients.objects.create(email='pavelkluevminsk@gmail.com', is_active=True)
        WeatherRecipients.objects.create(email='hitnik@gmail.com', is_active=True)
        WeatherRecipients.objects.create(email='django.odo@gmail.com', is_active=True)

    def test_put_feed_to_db(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        self.assertFalse(put_feed_to_db(feeds[0]))
        if len(feeds) > 1:
            self.assertTrue(put_feed_to_db(feeds[1]))

    def test_date_compare(self):
        d1 = datetime.datetime.utcnow()
        d2 = datetime.datetime.utcnow()+datetime.timedelta(hours=3)
        d3 = datetime.datetime.utcnow()+datetime.timedelta(days=1)
        # self.assertEqual(d1.date(), d2.date())
        self.assertNotEqual(d1.date(), d3.date())

    @override_settings(
        WEATHER_EMAIL_SMTP_HOST=env.WEATHER_EMAIL_SMTP_HOST,
        WEATHER_EMAIL_IMAP_PORT=env.WEATHER_EMAIL_IMAP_PORT,
        WEATHER_USE_TSL=env.WEATHER_USE_TSL,
        WEATHER_EMAIL_HOST_USER=env.WEATHER_EMAIL_HOST_USER,
        WEATHER_EMAIL_HOST_PASSWORD=env.WEATHER_EMAIL_HOST_PASSWORD
    )
    def test_send_weather_mail(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        msg = make_weather_hazard_message(feeds[0])
        recipients = get_weather_recipients()
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(send_weather_mail(msg, recipients))


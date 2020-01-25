from django.test import TestCase
from .utils import *
from .config import WEATHER_FEED_URL

# Create your tests here.

class TestUtils(TestCase):
    fixtures = ['hazard_feed/fixtures/hazard_levels.json']

    def setUp(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        feeds[0].save()

    def test_put_feed_to_db(self):
        feeds = parse_weather_feeds(WEATHER_FEED_URL)
        self.assertFalse(put_feed_to_db(feeds[0]))
        if len(feeds) > 1:
            self.assertTrue(put_feed_to_db(feeds[1]))

    def test_date_compare(self):
        d1 = datetime.datetime.utcnow()
        d2 = datetime.datetime.utcnow()+datetime.timedelta(hours=3)
        d3 = datetime.datetime.utcnow()+datetime.timedelta(days=1)
        self.assertEqual(d1.date(), d2.date())
        self.assertNotEqual(d1.date(), d3.date())



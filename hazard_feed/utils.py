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

def sendmail():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    dateString = format_date(yesterday, format='long', locale='ru')
    URLStart = settings.DJANGO_HOST
    url = 'http://' + URLStart + '/forums/1/' + str(yesterday.year) + '/' + str(yesterday.month) + '/' + str(
        yesterday.day)

    employees = Еmployees.objects.filter(isActive=True)
    topicsCount = Topics.objects.filter(datePost__date=yesterday).count()

    with mail.get_connection() as connection:
        for employee in employees:
            if employee.patronymic:
                fullName = employee.firstName + ' ' + employee.patronymic
            else:
                fullName = employee.firstName
            t = loader.get_template('forumTopics/email.html')
            context = {'fullName': fullName, 'dateString': dateString,
                       'url': url, 'topicsCount': topicsCount}
            html = t.render(context)
            text = 'Здравствуйте, ' + fullName + '. За ' + dateString + \
                   ' оставлено ' + str(topicsCount) + ' отзывов о Белтелеком.  Информация в прикрепленном файле или по ссылке:' + url
            subject = 'Отзывы о Белтелеком за ' + yesterday.strftime('%d.%m.%Y')
            msg = EmailMultiAlternatives(subject, text, 'ОДО <omc@main.beltelecom.by>', [employee.email])
            msg.attach_alternative(html, "text/html")
            msg.send()

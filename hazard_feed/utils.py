import re
import feedparser
import time
import datetime
import pytz
from .models import HazardLevels, HazardFeeds, WeatherRecipients
from django.conf import settings

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
    date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    local_tz = pytz.timezone(settings.TIME_ZONE)
    date = date.astimezone(local_tz)
    recipients = WeatherRecipients.objects.filter(is_active=True)
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

# def process_queue(q, logger):
#     logger.info("***** %s: Begin processing mail for django-helpdesk" % ctime())
#
#     if q.email_box_ssl or settings.QUEUE_EMAIL_BOX_SSL:
#         if not q.email_box_port:
#             q.email_box_port = 993
#         server = imaplib.IMAP4_SSL(q.email_box_host or
#                                    settings.QUEUE_EMAIL_BOX_HOST,
#                                    int(q.email_box_port))
#     else:
#         if not q.email_box_port:
#             q.email_box_port = 143
#         server = imaplib.IMAP4(q.email_box_host or
#                                settings.QUEUE_EMAIL_BOX_HOST,
#                                int(q.email_box_port))
#
#     logger.info("Attempting IMAP server login")
#
#     try:
#         server.login(q.email_box_user or
#                      settings.QUEUE_EMAIL_BOX_USER,
#                      q.email_box_pass or
#                      settings.QUEUE_EMAIL_BOX_PASSWORD)
#         server.select(q.email_box_imap_folder)
#     except imaplib.IMAP4.abort:
#         logger.error("IMAP login failed. Check that the server is accessible and that the username and password are correct.")
#         server.logout()
#         sys.exit()
#     except ssl.SSLError:
#         logger.error("IMAP login failed due to SSL error. This is often due to a timeout. Please check your connection and try again.")
#         server.logout()
#         sys.exit()
#
#     try:
#         # status, data = server.search(None, 'NOT', 'DELETED')
#         result, data = server.uid('search', None, "ALL")
#     except imaplib.IMAP4.error:
#         logger.error("IMAP retrieve failed. Is the folder '%s' spelled correctly, and does it exist on the server?" % q.email_box_imap_folder)
#     if data:
#         msgnums = data[0].split()
#         logger.info("Received %d messages from IMAP server" % len(msgnums))
#         for num in msgnums:
#             logger.info("Processing message %s" % num)
#             status, data = server.uid('fetch', num, '(RFC822)')
#             email_message = email.message_from_bytes(data[0][1])
#             fromAddr = email.utils.parseaddr(email_message['From'])[1]
#
#             full_message = encoding.force_text(data[0][1], errors='replace')
#             try:
#                 ticket = ticket_from_message(message=full_message, queue=q, logger=logger)
#             except TypeError:
#                 ticket = None  # hotfix. Need to work out WHY.
#             if ticket:
#                 server.uid('STORE', num, '+FLAGS', '\\Deleted')
#                 logger.info("Successfully processed message %s, deleted from IMAP server" % num)
#             else:
#                 server.uid('STORE', num, '-FLAGS', '(\Seen)')
#                 logger.warn("Message %s was not successfully processed, and will be left on IMAP server" % num)
#
#     server.expunge()
#     server.close()
#     server.logout()
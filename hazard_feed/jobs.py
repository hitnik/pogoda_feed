from django_rq import job
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from forumTopics.models import Employees, Topics, ForumUsers
import datetime
from django.conf import settings
from django.template import Context, loader
from babel.dates import format_date
import logging
import logging.config
import pdfkit

DICTLOGCONFIG={
"version":1,
        "handlers":{
            "fileHandler":{
                "class":"logging.FileHandler",
                "formatter":"myFormatter",
                "filename":"/home/odo/djhelpdesk/forumTopics/djhelpdeskclearDB.log"
            }
        },
        "loggers":{
            "clearDB":{
                "handlers":["fileHandler"],
                "level":"INFO",
            }
        },
        "formatters":{
            "myFormatter":{
                "format":"[%(asctime)s] - %(levelname)s - %(message)s"
            }
        }
}

@job
def sendmail():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    dateString = format_date(yesterday, format='long', locale='ru')
    URLStart = settings.DJANGO_HOST
    try:
        pdfkit.from_url('http://' + URLStart + '/forums/plain', '/home/odo/djhelpdesk/forums.pdf')
    except IOError as e:
        pass
    url = 'http://' + URLStart + '/forums/'

    employees = Employees.objects.filter(isActive=True)
    topicsCount = Topics.objects.filter(datePost__date=yesterday).count()
    topicsCountLastDigit = topicsCount % 10
    review = 'отзывов'
    left = 'оставлено'
    if topicsCountLastDigit == 1:
        review = "отзыв"
        left = 'оставлен'
    elif topicsCountLastDigit in [2, 3, 4]:
        review = 'отзыва'

    with mail.get_connection() as connection:
        for employee in employees:
            if employee.patronymic:
                fullName = employee.firstName + ' ' + employee.patronymic
            else:
                fullName = employee.firstName
            t = loader.get_template('forumTopics/email.html')
            context = {'fullName': fullName, 'dateString': dateString,
                       'url': url, 'topicsCount': topicsCount, 'review': review, 'left': left}
            html = t.render(context)
            text = 'Здравствуйте, ' + fullName + '. За ' + dateString + \
                   ' ' + left + ' ' + str(topicsCount) + ' ' + review + \
                   ' о Белтелеком. Информация в прикрепленном файле или по ссылке: ' + url
            subject = 'Отзывы о Белтелеком за ' + yesterday.strftime('%d.%m.%Y')
            msg = EmailMultiAlternatives(subject, text, 'ОДО <omc@main.beltelecom.by>', [employee.email])
            msg.attach_file('/home/odo/djhelpdesk/forums.pdf')
            msg.attach_alternative(html, "text/html")
            msg.send()

@job
def deleteOldTopics():
    logging.config.dictConfig(DICTLOGCONFIG)
    logger = logging.getLogger("clearDB")
    today = datetime.date.today()
    yearAgo = today
    yearAgo = yearAgo.replace(year=yearAgo.year - 1)
    deleteCandidates = Topics.objects.filter(datePost__datetz_lt=yearAgo).defer('id', 'user_id')
    logger.info("%d candidates for deletion" % (len(deleteCandidates)))
    count = 0;
    for topic in deleteCandidates:
        userCount = Topics.objects.filter(user__id=topic.user_id).count()
        if userCount == 1:
            count += 1
            ForumUsers.objects.filter(id=topic.user_id).delete()
        else:
            Topics.objects.filter(id=topic.id).delete()
    logger.info("delete %d topics, %d forumUsers" % (len(deleteCandidates), count))

    fileName = DICTLOGCONFIG['handlers']['fileHandler']['filename']
    linesToWrite = []
    countLines = 0
    with open(fileName, 'r') as f:
        lines = f.readlines()
        for line in list(reversed(lines)):
            linesToWrite.append(line)
            countLines += 1
            if countLines > 100: break
    with open(fileName, 'w') as f:
        for line in list(reversed(linesToWrite)):
            f.write(line)

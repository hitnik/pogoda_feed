#!/usr/bin/python

from __future__ import unicode_literals

from datetime import timedelta
import base64
import binascii
import email
import imaplib
import mimetypes
from os import listdir, unlink
from os.path import isfile, join
import poplib
import re
import socket
import ssl
import sys
from time import ctime

from bs4 import BeautifulSoup


from email_reply_parser import EmailReplyParser

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils import encoding, six, timezone

from helpdesk import settings
from helpdesk.lib import send_templated_mail, safe_template_context, process_attachments
from helpdesk.models import Queue, Ticket, HumanFriendlyID, TicketCC, FollowUp, IgnoreEmail
from helpdesk.models import Partner, PartnerEmail

from django.contrib.auth.models import User
import email
import logging
from email import parser
from mailbox import mboxMessage


STRIPPED_SUBJECT_STRINGS = [
    "Re: ",
    "Fw: ",
    "RE: ",
    "FW: ",
    "Automatic reply: ",
]


class Command(BaseCommand):

    def __init__(self):
        BaseCommand.__init__(self)

    help = 'Process django-helpdesk queues and process e-mails via POP3/IMAP or ' \
           'from a local mailbox directory as required, feeding them into the helpdesk.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet',
            action='store_true',
            dest='quiet',
            default=False,
            help='Hide details about each queue/message as they are processed',
        )

    def handle(self, *args, **kwargs):
        quiet = kwargs.get('quiet', False)
        process_email(quiet=quiet)


def process_email(quiet=False):
    for q in Queue.objects.filter(
            email_box_type__isnull=False,
            allow_email_submission=True):

        logger = logging.getLogger('django.helpdesk.queue.' + q.slug)
        if not q.logging_type or q.logging_type == 'none':
            logging.disable(logging.CRITICAL)  # disable all messages
        elif q.logging_type == 'info':
            logger.setLevel(logging.INFO)
        elif q.logging_type == 'warn':
            logger.setLevel(logging.WARN)
        elif q.logging_type == 'error':
            logger.setLevel(logging.ERROR)
        elif q.logging_type == 'crit':
            logger.setLevel(logging.CRITICAL)
        elif q.logging_type == 'debug':
            logger.setLevel(logging.DEBUG)
        if quiet:
            logger.propagate = False  # do not propagate to root logger that would log to console
        # logdir = q.logging_dir or '/var/log/helpdesk/'

        logdir =''

        handler = logging.FileHandler(join(logdir, q.slug + '_get_email.log'))
        logger.addHandler(handler)

        if not q.email_box_last_check:
            q.email_box_last_check = timezone.now() - timedelta(minutes=30)

        queue_time_delta = timedelta(minutes=q.email_box_interval or 0)

        # if (q.email_box_last_check + queue_time_delta) < timezone.now():
        #     process_queue(q, logger=logger)
        #     q.email_box_last_check = timezone.now()
        #     q.save()

        process_queue(q, logger=logger)

def process_queue(q, logger):
    logger.info("***** %s: Begin processing mail for django-helpdesk" % ctime())

    if q.email_box_ssl or settings.QUEUE_EMAIL_BOX_SSL:
        if not q.email_box_port:
            q.email_box_port = 993
        server = imaplib.IMAP4_SSL(q.email_box_host or
                                   settings.QUEUE_EMAIL_BOX_HOST,
                                   int(q.email_box_port))
    else:
        if not q.email_box_port:
            q.email_box_port = 143
        server = imaplib.IMAP4(q.email_box_host or
                               settings.QUEUE_EMAIL_BOX_HOST,
                               int(q.email_box_port))

    logger.info("Attempting IMAP server login")

    try:
        server.login(q.email_box_user or
                     settings.QUEUE_EMAIL_BOX_USER,
                     q.email_box_pass or
                     settings.QUEUE_EMAIL_BOX_PASSWORD)
        server.select(q.email_box_imap_folder)
    except imaplib.IMAP4.abort:
        logger.error("IMAP login failed. Check that the server is accessible and that the username and password are correct.")
        server.logout()
        sys.exit()
    except ssl.SSLError:
        logger.error("IMAP login failed due to SSL error. This is often due to a timeout. Please check your connection and try again.")
        server.logout()
        sys.exit()

    try:
        # status, data = server.search(None, 'NOT', 'DELETED')
        result, data = server.uid('search', None, "ALL")
    except imaplib.IMAP4.error:
        logger.error("IMAP retrieve failed. Is the folder '%s' spelled correctly, and does it exist on the server?" % q.email_box_imap_folder)
    if data:
        msgnums = data[0].split()
        logger.info("Received %d messages from IMAP server" % len(msgnums))
        for num in msgnums:
            logger.info("Processing message %s" % num)
            status, data = server.uid('fetch', num, '(RFC822)')
            email_message = email.message_from_bytes(data[0][1])
            fromAddr = email.utils.parseaddr(email_message['From'])[1]

            full_message = encoding.force_text(data[0][1], errors='replace')
            try:
                ticket = ticket_from_message(message=full_message, queue=q, logger=logger)
            except TypeError:
                ticket = None  # hotfix. Need to work out WHY.
            if ticket:
                server.uid('STORE', num, '+FLAGS', '\\Deleted')
                logger.info("Successfully processed message %s, deleted from IMAP server" % num)
            else:
                server.uid('STORE', num, '-FLAGS', '(\Seen)')
                logger.warn("Message %s was not successfully processed, and will be left on IMAP server" % num)

    server.expunge()
    server.close()
    server.logout()


def decodeUnknown(charset, string):

    if type(string) is not str:
        if not charset:
            try:
                return str(string, encoding='utf-8', errors='replace')
            except UnicodeError:
                return str(string, encoding='iso8859-1', errors='replace')
        return str(string, encoding=charset, errors='replace')
    return string


def decode_mail_headers(string):
    decoded = email.header.decode_header(string)
    return u' '.join([str(msg, encoding=charset, errors='replace') if charset else str(msg) for msg, charset in decoded])


def ticket_from_message(message, queue, logger):
    # 'message' must be an RFC822 formatted message.
    # парсим сообщение
    message = email.message_from_string(message)
    # получаем тему письма
    subject = message.get('subject', _('Comment from e-mail'))
    # пытаемся декодировать тему письма
    subject = decode_mail_headers(decodeUnknown(message.get_charset(), subject))
    # удаляем заголовок письма
    for affix in STRIPPED_SUBJECT_STRINGS:
        subject = subject.replace(affix, "")
    # разбиваем заголовок на слова
    subject = subject.strip()

    # получаем отправителя
    # можно сюда перенести проверку на отправителя для экономии ресурсов
    sender = message.get('from', _('Unknown Sender'))
    sender = decode_mail_headers(decodeUnknown(message.get_charset(), sender))
    sender_email = email.utils.parseaddr(sender)[1]
    if PartnerEmail.objects.filter(email=sender_email, partner__isActive=True).exists():
        # проверяем есть ли адреса копий сообщений
        # и если есть, то возвращаем массив адресов
        cc = message.get_all('cc', None)
        if cc:
            # first, fixup the encoding if necessary
            cc = [decode_mail_headers(decodeUnknown(message.get_charset(), x)) for x in cc]
            # get_all checks if multiple CC headers, but individual emails may be comma separated too
            tempcc = []
            for hdr in cc:
                tempcc.extend(hdr.split(','))
            # используем множество, чтобы исключить дубликаты
            cc = set([x.strip() for x in tempcc])

        # проверяем адрес на игнор лист
        for ignore in IgnoreEmail.objects.filter(Q(queues=queue) | Q(queues__isnull=True)):
            if ignore.test(sender_email):
                if ignore.keep_in_mailbox:
                    # By returning 'False' the message will be kept in the mailbox,
                    # and the 'True' will cause the message to be deleted.
                    return False
                return True

        # проверяем, есть ли в теме письма номер уже открытого тикета
        # matchobj = re.match(r".*\[" + queue.slug + "-(?P<id>\d+)\]", subject)
        matchobj = re.match(r".*\[(?P<id>\d{9,9})\]", subject)
        if matchobj:
            print(matchobj.group('id'))
            # это ответ или дополнение, парсим номер тикета
            tmp=Ticket.objects.filter(humanID__humanFriendlyID=matchobj.group('id')).only('id').first()
            ticket = tmp.id
            logger.info("Matched tracking ID %s" % (ticket))
        else:
            logger.info("No tracking ID matched.")
            ticket = None
        # тело письма и прикрепленные файлы
        body = None
        counter = 0
        files = []


        for part in message.walk():
            # если тип письма мультипарт то пропускаем
            if part.get_content_maintype() == 'multipart':
                continue


            name = part.get_param("name")
            if name:
                name = email.utils.collapse_rfc2231_value(name)

            if part.get_content_maintype() == 'text' and name is None:
                if part.get_content_subtype() == 'plain':
                    body = EmailReplyParser.parse_reply(
                        decodeUnknown(part.get_content_charset(), part.get_payload(decode=True))
                     )
                    # workaround to get unicode text out rather than escaped text
                    try:
                        body = body.encode('ascii').decode('unicode_escape')
                    except UnicodeEncodeError:
                        body.encode('utf-8')
                    logger.debug("Discovered plain text MIME part")
                else:
                    files.append(
                        SimpleUploadedFile(_("email_html_body.html"), encoding.smart_bytes(part.get_payload()), 'text/html')
                    )
                    logger.debug("Discovered HTML MIME part")
            else:
                if not name:
                    ext = mimetypes.guess_extension(part.get_content_type())
                    name = "part-%i%s" % (counter, ext)
                payload = part.get_payload()
                if isinstance(payload, list):
                    payload = payload.pop().as_string()
                payloadToWrite = payload
                # check version of python to ensure use of only the correct error type

                non_b64_err = TypeError
                try:
                    logger.debug("Try to base64 decode the attachment payload")
                    payloadToWrite = base64.decodebytes(payload)
                except non_b64_err:
                    logger.debug("Payload was not base64 encoded, using raw bytes")
                    payloadToWrite = payload
                files.append(SimpleUploadedFile(name, part.get_payload(decode=True), mimetypes.guess_type(name)[0]))
                logger.debug("Found MIME attachment %s" % name)

            counter += 1

        if not body:
            mail = BeautifulSoup(part.get_payload(), "lxml")
            if ">" in mail.text:
                body = mail.find('body')
                body = body.text
                body = body.encode('ascii', errors='ignore')
            else:
                body = mail.text


        if ticket:
            try:
                t = Ticket.objects.get(id=ticket)
            except Ticket.DoesNotExist:
                logger.info("Tracking ID %s-%s not associated with existing ticket. Creating new ticket." % (queue.slug, ticket))
                ticket = None
            else:
                logger.info("Found existing ticket with Tracking ID %s-%s" % (t.queue.slug, t.id))
                if t.status == Ticket.CLOSED_STATUS:
                    t.status = Ticket.REOPENED_STATUS
                    t.save()
                new = False

        smtp_priority = message.get('priority', '')
        smtp_importance = message.get('importance', '')
        high_priority_types = {'high', 'important', '1', 'urgent'}
        priority = 2 if high_priority_types & {smtp_priority, smtp_importance} else 3

        if ticket is None:
            if settings.QUEUE_EMAIL_BOX_UPDATE_ONLY:
                return None
            new = True
            t = Ticket.objects.create(
                title=subject,
                queue=queue,
                submitter_email=sender_email,
                created=timezone.now(),
                description=body,
                priority=priority,
            )
            logger.debug("Created new ticket %s-%s" % (t.queue.slug, t.id))

        if cc:
            # get list of currently CC'd emails
            current_cc = TicketCC.objects.filter(ticket=ticket)
            current_cc_emails = [x.email for x in current_cc if x.email]
            # get emails of any Users CC'd to email, if defined
            # (some Users may not have an associated email, e.g, when using LDAP)
            current_cc_users = [x.user.email for x in current_cc if x.user and x.user.email]
            # ensure submitter, assigned user, queue email not added
            other_emails = [queue.email_address]
            if t.submitter_email:
                other_emails.append(t.submitter_email)
            if t.assigned_to:
                other_emails.append(t.assigned_to.email)
            current_cc = set(current_cc_emails + current_cc_users + other_emails)
            # first, add any User not previously CC'd (as identified by User's email)
            all_users = User.objects.all()
            all_user_emails = set([x.email for x in all_users])
            users_not_currently_ccd = all_user_emails.difference(set(current_cc))
            users_to_cc = cc.intersection(users_not_currently_ccd)
            for user in users_to_cc:
                tcc = TicketCC.objects.create(
                    ticket=t,
                    user=User.objects.get(email=user),
                    can_view=True,
                    can_update=False
                )
                tcc.save()
            # then add remaining emails alphabetically, makes testing easy
            new_cc = cc.difference(current_cc).difference(all_user_emails)
            new_cc = sorted(list(new_cc))
            for ccemail in new_cc:
                tcc = TicketCC.objects.create(
                    ticket=t,
                    email=ccemail.replace('\n', ' ').replace('\r', ' '),
                    can_view=True,
                    can_update=False
                )
                tcc.save()

        f = FollowUp(
            ticket=t,
            title=_('E-Mail Received from %(sender_email)s' % {'sender_email': sender_email}),
            date=timezone.now(),
            public=True,
            comment=body,
        )

        if t.status == Ticket.REOPENED_STATUS:
            f.new_status = Ticket.REOPENED_STATUS
            f.title = _('Ticket Re-Opened by E-Mail Received from %(sender_email)s' % {'sender_email': sender_email})

        f.save()
        logger.debug("Created new FollowUp for Ticket")

        if six.PY2:
            logger.info(("[%s-%s] %s" % (t.queue.slug, t.id, t.title,)).encode('ascii', 'replace'))
        elif six.PY3:
            logger.info("[%s-%s] %s" % (t.queue.slug, t.id, t.title,))

        attached = process_attachments(f, files)
        for att_file in attached:
            logger.info("Attachment '%s' (with size %s) successfully added to ticket from email." % (att_file[0], att_file[1].size))

        context = safe_template_context(t)

        if new:
            if sender_email:
                send_templated_mail(
                    'newticket_submitter',
                    context,
                    recipients=sender_email,
                    sender=settings.DEFAULT_FROM_EMAIL,
                    fail_silently=True,
                )
            if queue.new_ticket_cc:
                send_templated_mail(
                    'newticket_cc',
                    context,
                    recipients=queue.new_ticket_cc,
                    sender=queue.from_address,
                    fail_silently=True,
                )
            if queue.updated_ticket_cc and queue.updated_ticket_cc != queue.new_ticket_cc:
                send_templated_mail(
                    'newticket_cc',
                    context,
                    recipients=queue.updated_ticket_cc,
                    sender=queue.from_address,
                    fail_silently=True,
                )
        else:
            context.update(comment=f.comment)
            if t.assigned_to:
                send_templated_mail(
                    'updated_owner',
                    context,
                    recipients=t.assigned_to.email,
                    sender=queue.from_address,
                    fail_silently=True,
                )
            if queue.updated_ticket_cc:
                send_templated_mail(
                    'updated_cc',
                    context,
                    recipients=queue.updated_ticket_cc,
                    sender=queue.from_address,
                    fail_silently=True,
                )

        return t
    else:return None


if __name__ == '__main__':
    process_email()

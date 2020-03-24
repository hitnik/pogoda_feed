from rest_framework.views import APIView
from rest_framework import generics
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ValidationError
import django_rq
from django.conf import settings
from .utils import get_session_obj
from .models import EmailActivationCode


class ScheduledJobsView(APIView):
    def get(self, request, format=None):
        data = {}
        rq_queues = settings.RQ_QUEUES
        for queue, value in rq_queues.items():
            scheduler = django_rq.get_scheduler(queue)
            data[queue] = []
            for job in scheduler.get_jobs():
                job_data = {}
                job_data['id'] = job.get_id()
                job_data['func_name'] = job.func_name
                data[queue].append(job_data)

        return Response(data)



class NewsletterSubscribeAPIView(generics.CreateAPIView):
    serializer_class = WeatherRecipientsMailTitleSerializer

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            codes = exc.get_codes()
            if 'email' in codes:
                if 'unique' in codes['email']:
                    serializer = self.get_serializer()
                    email = self.get_serializer_context()['request'].POST.get('email')
                    model = getattr(serializer.Meta, 'model')
                    obj = model.objects.get(email=email)
                    if obj.is_active:
                        return Response(status=status.HTTP_302_FOUND)
                    else:
                        expires = settings.CODE_EXPIRATION_TIME
                        data = {'expires': expires}
                        session = get_session_obj(self.request)
                        obj.title = self.get_serializer_context()['request'].POST.get('title')
                        obj.save()
                        EmailActivationCode.objects.create(session=session, target=obj)
                        return Response(data=data, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.status_code = status.HTTP_200_OK
        expires = settings.CODE_EXPIRATION_TIME
        response.data = {'expires': expires}
        return response

    def perform_create(self, serializer):
        instance = serializer.save()
        session = get_session_obj(self.request)
        EmailActivationCode.objects.create(session=session, target=instance)

class ActivateSubscribe(APIView):

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = ActivationCodeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            code = serializer.data['code']
            session = get_session_obj(request)
            if EmailActivationCode.objects.filter(session=session).exixts():
                activation = EmailActivationCode.objects.get(session=session)
                is_activated = activation.activate(code)
                if is_activated:
                    return Response(status=status.HTTP_200_OK)
                else: return Response(status=status.HTTP_400_BAD_REQUEST)
            else:return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)
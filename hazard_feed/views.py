from rest_framework.views import APIView
from rest_framework import generics
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
import django_rq
from django.conf import settings
from .utils import get_session_obj
from .models import EmailActivationCode, WeatherRecipients
from django.urls import reverse_lazy
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
import jwt
from django.conf import  settings

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


@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='newsletter_subscribe',
                                                operation_description="Subscripe Newsletter view",
                                                responses={status.HTTP_200_OK: SubcribeResponseSerializer,
                                                           status.HTTP_302_FOUND: None}
                  ))
class NewsletterSubscribeAPIView(generics.GenericAPIView):
    serializer_class = SubscribeSerialiser

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def create_code_response(self, recipient):
        code = EmailActivationCode.objects.create(target=recipient, is_activate=True)
        token = jwt.encode({'id': code.id.__str__(), 'exp': code.date_expiration},
                           settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        data = {'expires': code.date_expiration,
                'token': token,
                'code_confirm': reverse_lazy('hazard_feed:activate_subscribe')
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def post(self,request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            title = serializer.validated_data.get('title')
            queryset = self.get_queryset()
            if queryset.filter(email=email).exists():
                obj = queryset.get(email=email)
                if obj.is_active:
                    return Response(status=status.HTTP_302_FOUND)
                else:
                    obj.title = title
                    obj.save()
                    return self.create_code_response(obj)
            else:
                obj = WeatherRecipients.objects.create(email=email, title=title)
                return self.create_code_response(obj)
            return Response(status=status.HTTP_200_OK)




@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='newsletter_unsubscribe',
                                                operation_description="Unsubscripe Newsletter view",
                                                responses={status.HTTP_200_OK: SubcribeResponseSerializer}
                  ))
class NewsletterUnsubscribeAPIView(generics.GenericAPIView):
    serializer_class = WeatherRecipientsMailSerializer

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and exc.detail['email'][0] == 'email does not exist':
            exc.status_code = status.HTTP_404_NOT_FOUND
        return super().handle_exception(exc)

    def create_code_response(self, recipient):
        code = EmailActivationCode.objects.create(target=recipient, is_activate=False)
        token = jwt.encode({'id': code.id.__str__(), 'exp': code.date_expiration},
                           settings.SECRET_KEY, algorithm='HS256').decode('utf-8')
        data = {'expires': code.date_expiration,
                'token': token,
                'code_confirm': reverse_lazy('hazard_feed:deactivate_subscribe')
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            target = WeatherRecipients.objects.get(email=email)
            if target.is_active:
                return self.create_code_response(target)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='activate_subscribe',
                                                operation_description="Subscribe Newsletter code confirmation view",
                                                responses={status.HTTP_200_OK: SuccesResponseSerializer}
                  ))
class SubscribeActivationAPIView(generics.GenericAPIView):
    serializer_class = ActivationCodeSerializer

    def perform_action(self, instance, code):
       result = instance.activate_deactivate(code)
       return result

    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                data = jwt.decode(serializer.data['token'], settings.SECRET_KEY, algorithm='HS256')
            except jwt.ExpiredSignatureError:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Code is expired'})
            except jwt.InvalidTokenError:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid token'})
            code = serializer.data['code']
            id = data['id']
            if EmailActivationCode.objects.filter(id=id).exists():
                activation = EmailActivationCode.objects.get(id=id)
                if self.perform_action(activation, code):
                    serializer = SuccesResponseSerializer(data={'ok':True})
                    if serializer.is_valid():
                        return Response(status=status.HTTP_200_OK, data=serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid Code'})



@method_decorator(name='post',
                  decorator=swagger_auto_schema(operation_id='deactivate_subscribe',
                                                operation_description="Unsubscribe Newsletter code confirmation view",
                                                responses={status.HTTP_200_OK: SuccesResponseSerializer}
                  ))
class SubscribeDeactivationAPIView(SubscribeActivationAPIView):

    def post(self, request, format=None):
        return self.post(request, format)

    def perform_action(self, instance, code):
        result = instance.activate_deactivate(code)
        return result

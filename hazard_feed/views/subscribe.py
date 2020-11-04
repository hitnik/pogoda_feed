from rest_framework import generics, viewsets
from django.http import Http404
import django_rq
from redis.exceptions import ConnectionError
from hazard_feed.serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from hazard_feed.models import (EmailActivationCode, WeatherRecipients,
                                # WeatherRecipientsEditCandidate, EditValidationCode
                                )
from django.urls import reverse_lazy
from hazard_feed.jobs import send_email_code_activate


class NewsletterSubscribeAPIView(generics.GenericAPIView):
    serializer_class = SubscribeSerialiser
    validate_url = reverse_lazy('hazard_feed:code_validate')

    def get_queryset(self):
        return WeatherRecipients.objects.all()

    def serialized_data(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            title = serializer.validated_data.get('title')
            levels = list(serializer.validated_data.get('hazard_levels'))
            if len(levels) == 0:
                levels = list(HazardLevels.objects.all().values_list('id', flat=True))
            return email, title, levels

    def generate_code(self):
        return EmailActivationCode.objects.create()

    def create_code_response(self, code, target):
        data = {'expires': int(code.date_expiration.timestamp() * 1000),
                'target_uid': target.uuid,
                'code_confirm': self.validate_url
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def send_notify(self, code, recipient):
        try:
            queue = django_rq.get_queue()
            queue.enqueue(send_email_code_activate, code, [recipient])
        except ConnectionError:
            send_email_code_activate(code, [recipient])

    @csrf_exempt
    def post(self, request, format=None):
        email, title, levels = self.serialized_data(request)
        queryset = self.get_queryset()
        if queryset.filter(email=email).exists():
            obj = queryset.get(email=email)
            if obj.is_active:
                return Response(status=status.HTTP_302_FOUND)
            else:
                obj.title = title
                obj.hazard_levels.clear()
                obj.hazard_levels.add(*levels)
                if obj.code:
                    obj.code.delete()
                code = self.generate_code()
                obj.code = code
                obj.save()
                self.send_notify(code.code, obj.email)
                return self.create_code_response(code, obj)
        else:
            obj = WeatherRecipients.objects.create(email=email, title=title)
            obj.hazard_levels.add(*levels)
            code = self.generate_code()
            obj.code = code
            obj.save()
            self.send_notify(code.code, obj.email)
            return self.create_code_response(code, obj)



class NewsletterSubscribeEditApiView(NewsletterSubscribeAPIView):

    def generate_code(self, obj):
        return EditValidationCode.objects.create(target=obj)

    @csrf_exempt
    def post(self, request, format=None):
        email, title, levels = self.serialized_data(request)
        queryset = self.get_queryset()
        if queryset.filter(email=email).exists():
            obj = queryset.get(email=email)
            if obj.is_active:
                if WeatherRecipientsEditCandidate.objects.filter(target__email=email).exists():
                    WeatherRecipientsEditCandidate.objects.get(target__email=email).delete()
                candidate = WeatherRecipientsEditCandidate.objects.create(
                    target=obj,
                    title=title,
                )
                candidate.hazard_levels.add(*levels)
                return self.create_code_response(self.generate_code(candidate), reverse_lazy('hazard_feed:code_validate'))
        return Response(status=status.HTTP_404_NOT_FOUND)


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

        data = {'expires': int(code.date_expiration.timestamp() * 1000),
                'token': token,
                'code_confirm': reverse_lazy('hazard_feed:code_validate')
                }
        response_serializer = SubcribeResponseSerializer(data=data)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @csrf_exempt
    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email')
            target = WeatherRecipients.objects.get(email=email)
            if target.is_active:
                return self.create_code_response(target)
            else:
                return Response(status=status.HTTP_303_SEE_OTHER)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SubscribeValidationAPIView(generics.GenericAPIView):
    serializer_class = ActivationCodeSerializer

    def response_success(self):
        message = 'Your newsletter subscription has been activated'
        serializer = SuccesResponseSerializer(data={'ok': True, 'message': message})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def get_serialized_data(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            code = serializer.data['code']
            uid = serializer.data['target_uid']
            return code, uid

    @csrf_exempt
    def post(self, request, format=None):
        code, uid = self.get_serialized_data(request)
        try:
            obj = WeatherRecipients.objects.get(uuid=uid)
        except WeatherRecipients.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid uid'})
        if obj.code.is_valid(code):
           obj.is_active = True
           return  self.response_success()
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'Error': 'Invalid Code'})

class WeatherRecipientsRetrieveAPIView(generics.RetrieveAPIView):
    http_method_names = [u'trace', u'head', u'options', u'post']
    queryset = WeatherRecipients.objects.all().filter(is_active=True)
    serializer_class_response = WeatherRecipientsModelSerializer
    serializer_class = WeatherRecipientsMailSerializer

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.serializer_class_response(self.object)
        return Response(serializer.data)

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        if queryset is None:
            queryset = self.get_queryset()

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if email is not None:
            queryset = queryset.filter(email=email)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404("No %(verbose_name)s found matching the query" %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


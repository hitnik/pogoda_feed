from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

class NewsletterSubscribeAPIView(generics.CreateAPIView):
    serializer_class = WeatherRecipientsMailTitleSerializer

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            codes = exc.get_codes()
            if 'email' in codes:
                if 'unique' in codes['email']:
                    serializer = self.get_serializer()
                    email = self.get_serializer_context()['request'].POST.get('email')
                    title = self.get_serializer_context()['request'].POST.get('title')
                    model = getattr(serializer.Meta, 'model')
                    obj = model.objects.get(email=email)
                    return Response({}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.status_code = status.HTTP_200_OK
        response.data = {}
        return response

class ActivateSubscribe(APIView):
    pass

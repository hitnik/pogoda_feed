from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

class NewsletterSubscribeAPIView(generics.CreateAPIView):
    serializer_class = WeaWeatherRecipientsMailTitleSerializer


    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            codes = exc.get_codes()
            if 'email' in codes:
                if 'unique' in codes['email']:
                    serializer = self.get_serializer()
                    self.perform_create(serializer, exists=True)
                    return Response({}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.status_code = status.HTTP_200_OK
        response.data = {}
        return response

    def perform_create(self, serializer, exists=False):
        if not exists:
            super().perform_create(serializer)
        else:
            pass

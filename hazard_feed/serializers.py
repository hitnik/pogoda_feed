from rest_framework import serializers
from .models import WeatherRecipients

class WeatherRecipientsMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRecipients
        fields = ['email']

class WeatherRecipientsMailTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRecipients
        fields = ['email', 'title']

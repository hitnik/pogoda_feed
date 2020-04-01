from rest_framework import serializers
from .models import WeatherRecipients
from django.conf import settings
from rest_framework import status


class WeatherRecipientsMailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)

    def validate_email(self, value):
        try:
            obj = WeatherRecipients.objects.get(email=value)
        except model.DoesNotExist:
            raise serializers.ValidationError(detail='email does not exist')
        return value


class WeatherRecipientsMailTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRecipients
        fields = ['email', 'title']

class ActivationCodeSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_blank=True,
                                 max_length=settings.ACTIVATION_CODE_LENTH,
                                 min_length=settings.ACTIVATION_CODE_LENTH)

    def create(self, validated_data):
        return validated_data

    def validate_code(self, value):
        try:
            code = int(value)
        except ValueError:
            raise serializers.ValidationError('Not a digit')
        return value




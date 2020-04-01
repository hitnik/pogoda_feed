from rest_framework import serializers
from .models import WeatherRecipients
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError

class ValidationError404(ValidationError):
    status_code = status.HTTP_404_NOT_FOUND

class WeatherRecipientsMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRecipients
        fields = ['email']

    def validate_email(self, value):
        model = getattr(self.Meta, 'model')
        try:
            obj = model.objects.get(email=value)
        except model.DoesNotExist:
            raise ValidationError404(detail='email does not exist')
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




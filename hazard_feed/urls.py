from django.urls import path
from .views import *

app_name = 'hazard_feed'

urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter')
]


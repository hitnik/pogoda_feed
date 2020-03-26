from django.urls import path
from .views import *

app_name = 'hazard_feed'

urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/jobs', ScheduledJobsView.as_view(), name='jobs'),
    path('v1/activate', SubscribeActivationAPIView.as_view(), name='activate_subscribe'),
]


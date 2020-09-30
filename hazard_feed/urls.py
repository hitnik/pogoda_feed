from django.urls import path
from .views.subscribe import *
from .views.warnings import *
app_name = 'hazard_feed'



urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/unsubscribe_newsletter', NewsletterUnsubscribeAPIView.as_view(), name='unsubscribe_newsletter'),
    path('v1/code-validate', CodeValidationAPIView.as_view(), name='code_validate'),
    path('v1/warnings/list', HazardListAPIView.as_view(), name='warnings_list'),
]


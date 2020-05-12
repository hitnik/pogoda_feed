from django.urls import path
from .views import *
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer
from rest_framework_swagger.views import get_swagger_view


app_name = 'hazard_feed'

schema_view = get_schema_view(
    title='Weather hazard feeds API',
    version= '1.0.0',
    renderer_classes=[JSONOpenAPIRenderer],
)

swagger_view = get_swagger_view(
    title='Weather hazard feeds API',
)

urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/unsubscribe_newsletter', NewsletterUnsubscribeAPIVIEW.as_view(), name='unsubscribe_newsletter'),
    # path('v1/jobs', ScheduledJobsView.as_view(), name='jobs'),
    path('v1/activate', SubscribeActivationAPIView.as_view(), name='activate_subscribe'),
    path('v1/deactivate', SubscribeDeactivationAPIView.as_view(), name='deactivate_subscribe'),
    path('openapi', schema_view, name='openapi-schema'),
    path('', swagger_view, name='docs'),

]


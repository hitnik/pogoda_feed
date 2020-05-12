from django.urls import path, re_path
from .views import *
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework import permissions
from drf_yasg.views import get_schema_view as yasg_get_schema_view
from drf_yasg import openapi

app_name = 'hazard_feed'

schema_view = get_schema_view(
    title='Weather hazard feeds API',
    version= '1.0.0',
    renderer_classes=[JSONOpenAPIRenderer],
)

yasg_schema_view = yasg_get_schema_view(
   openapi.Info(
      title="Weather API",
      default_version='v1',
      description="Weather hazard feeds API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('v1/subscribe_newsletter', NewsletterSubscribeAPIView.as_view(), name='subscribe_newsletter'),
    path('v1/unsubscribe_newsletter', NewsletterUnsubscribeAPIVIEW.as_view(), name='unsubscribe_newsletter'),
    # path('v1/jobs', ScheduledJobsView.as_view(), name='jobs'),
    path('v1/activate', SubscribeActivationAPIView.as_view(), name='activate_subscribe'),
    path('v1/deactivate', SubscribeDeactivationAPIView.as_view(), name='deactivate_subscribe'),
    path('openapi', schema_view, name='schema-openapi'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', yasg_schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', yasg_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', yasg_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]


"""
ASGI config for pogoda_feed project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""


# uvicorn pogoda_feed.asgi:application --ws websockets --http httptools
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker pogoda_feed.asgi:application

from .wsgi import *
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import hazard_feed.routing
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pogoda_feed.settings')

application = ProtocolTypeRouter({
  'http': get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            hazard_feed.routing.websocket_urlpatterns
        )
    ),
})
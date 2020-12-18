"""
ASGI config for pogoda_feed project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

from .wsgi import *
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import hazard_feed.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pogoda_feed.settings')

application = ProtocolTypeRouter({
  "websocket": AuthMiddlewareStack(
        URLRouter(
            hazard_feed.routing.websocket_urlpatterns
        )
    ),
})
"""
ASGI config for pogoda_feed project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import hazard_feed.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pogoda_feed.settings')

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            hazard_feed.routing.websocket_urlpatterns
        )
    ),
})
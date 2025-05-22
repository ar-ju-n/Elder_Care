from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import chat.routing
import forum.routing
import jobs.routing
import accounts.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
chat.routing.websocket_urlpatterns +
            forum.routing.websocket_urlpatterns +
            jobs.routing.websocket_urlpatterns +
            accounts.routing.websocket_urlpatterns
        )
    ),
})

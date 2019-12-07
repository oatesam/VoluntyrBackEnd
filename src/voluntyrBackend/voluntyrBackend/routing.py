from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from chat import routing
from chat.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    'websocket': JWTAuthMiddleware(
        URLRouter(
            routing.websocket_urlpatterns
        )),
})

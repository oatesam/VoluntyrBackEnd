from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from voluntyr.chat import routing as chat

application = ProtocolTypeRouter({
    'websocket': URLRouter(
            chat.websocket_urlpatterns
        )
})

from django.db import close_old_connections
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class JWTAuthMiddleware:
    """
    Custom middleware that verifies the JWT and adds the user_id to the scope
    """

    def __init__(self, inner):
        self.inner = inner
        self.auth = JWTAuthentication()

    def __call__(self, scope):
        close_old_connections()

        headers = dict(scope['headers'])
        if b'authorization' in headers:
            try:
                raw_token = bytes(headers[b'authorization']).decode('utf-8').split()[1]
                valid_token = self.auth.get_validated_token(raw_token)
                user_id = valid_token.get('user_id')
                return self.inner(dict(scope, user_id=user_id))
            except IndexError:
                return self.inner(dict(scope, auth_error="Invalid token format."))
            except InvalidToken:
                return self.inner(dict(scope, auth_error="Invalid token."))
        return self.inner(dict(scope, auth_error="Missing authorization headers."))

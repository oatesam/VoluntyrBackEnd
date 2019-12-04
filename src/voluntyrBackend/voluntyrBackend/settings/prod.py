from .shared import *
import dj_database_url

SECRET_KEY = os.environ.get('VOL_SECRET_KEY')
ACCOUNT_SECURITY_API_KEY = 'GuOHIvasIHAUTMk0AUcaVs8gE4lHRtGG'

ALLOWED_HOSTS = [
    'voluntyr-backend-stg.herokuapp.com',
    'voluntyr-backend-prod.herokuapp.com'
]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

FRONTEND_HOST = 'https://voluntyr.herokuapp.com'


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

# TODO story-57: Add heroku redis resource
CHANNEL_LAYERS = {
    "default": {
            "BACKEND": "asgi_redis.RedisChannelLayer",
            "CONFIG": {
                "hosts": ['redis://localhost:6379'],
            },
            "ROUTING": "chat.routing.channel_routing",
        },
}

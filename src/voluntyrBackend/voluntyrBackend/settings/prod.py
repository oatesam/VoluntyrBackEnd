from .shared import *
import dj_database_url

SECRET_KEY = os.environ.get('VOL_SECRET_KEY')
ACCOUNT_SECURITY_API_KEY='Sq5dZocEP1yVIEq6kHXcplyps7lbpWi1'

ALLOWED_HOSTS = [
    'voluntyr-backend-stg.herokuapp.com',
    'voluntyr-backend-prod.herokuapp.com'
]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

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

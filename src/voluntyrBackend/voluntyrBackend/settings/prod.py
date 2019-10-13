from .shared import *
import dj_database_url
import hero

SECRET_KEY = os.environ.get('VOL_SECRET_KEY')

ALLOWED_HOSTS = ['voluntyr-backend-stg.heroku.com']

# TODO: Setup PostgreSQL db on heroku and set settings here
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

from .shared import *

# TODO: Set env var for secret_key
SECRET_KEY = os.environ.get('VOL_SECRET_KEY')

# TODO: Add allowed hosts
ALLOWED_HOSTS = []

# TODO: Setup PostgreSQL db on heroku and set settings here
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

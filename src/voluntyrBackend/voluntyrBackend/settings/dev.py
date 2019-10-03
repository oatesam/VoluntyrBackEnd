from .shared import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v=3z4059_@x6iezx&x$*hi!t%n!(r#!j!=32lg9j!m-=bz3h*$'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}





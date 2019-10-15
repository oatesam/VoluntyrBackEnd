#!/usr/bin/env bash
cd ../voluntyrBackend/
python manage.py migrate
gunicorn voluntyrBackend.wsgi:application --bind 0.0.0.0:$PORT
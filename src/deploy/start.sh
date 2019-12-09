#!/usr/bin/env bash
cd ../voluntyrBackend/
python manage.py migrate
daphne voluntyrBackend.asgi:application -p $PORT -b 0.0.0.0 -v2